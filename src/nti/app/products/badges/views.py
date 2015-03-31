#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from . import MessageFactory as _

import urllib
import requests
from io import BytesIO
from collections import Mapping

from zope import component
from zope import interface
from zope.container.contained import Contained
from zope.traversing.interfaces import IPathAdapter

from pyramid.view import view_config
from pyramid.view import view_defaults
from pyramid.interfaces import IRequest
from pyramid import httpexceptions as hexc

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.appserver.workspaces.interfaces import IUserService

from nti.badges.interfaces import IBadgeManager
from nti.badges.openbadges.interfaces import IBadgeClass
from nti.badges.openbadges.interfaces import IBadgeAssertion
from nti.badges.openbadges.utils.badgebakery import bake_badge

from nti.dataserver import authorization as nauth
from nti.dataserver.authorization_acl import ace_allowing
from nti.dataserver.authorization_acl import acl_from_aces

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import IDataserverFolder
from nti.dataserver.interfaces import EVERYONE_USER_NAME

from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.externalization import to_external_object

from .utils import get_badge_image_url
from .interfaces import IBadgesWorkspace

from . import OPEN_BADGES_VIEW
from . import OPEN_ASSERTIONS_VIEW

from . import is_locked
from . import get_user_email
from . import update_assertion
from . import is_email_verified


ALL = getattr(StandardExternalFields, 'ALL', ())

@interface.implementer(IPathAdapter)
@component.adapter(IUser, IRequest)
def BadgesWorkspacePathAdapter(context, request):
	service = IUserService(context)
	workspace = IBadgesWorkspace(service)
	return workspace

@interface.implementer(IPathAdapter)
class BadgeAdminPathAdapter(Contained):

	__name__ = 'BadgeAdmin'

	def __init__(self, context, request):
		self.context = context
		self.request = request
		self.__parent__ = context

@view_config(route_name='objects.generic.traversal',
			 name=OPEN_BADGES_VIEW,
			 renderer='rest',
			 request_method='GET',
			 context=IDataserverFolder)
class OpenBadgeView(object):

	def __init__(self, request):
		self.request = request

	def __call__(self):
		request = self.request
		badge = request.subpath[0] if request.subpath else ''
		if not badge:
			raise hexc.HTTPNotFound()

		manager = component.getUtility(IBadgeManager)
		result = manager.get_badge(badge)
		if result is not None:
			return IBadgeClass(result)

		raise hexc.HTTPNotFound(_('Badge not found.'))

@interface.implementer(IPathAdapter)
@component.adapter(IDataserverFolder, IRequest)
class OpenAssertionsPathAdapter(Contained):

	def __init__(self, dataserver, request):
		self.__parent__ = dataserver
		self.__name__ = OPEN_ASSERTIONS_VIEW

	def __getitem__(self, assertion_id):
		if not assertion_id:
			raise hexc.HTTPNotFound()

		assertion_id = urllib.unquote(assertion_id)
		manager = component.getUtility(IBadgeManager)
		result = manager.get_assertion_by_id(assertion_id)
		if result is not None:
			result = IBadgeAssertion(result)
			result. __acl__ = acl_from_aces(
								ace_allowing(EVERYONE_USER_NAME, nauth.ACT_READ))
			return result
		raise KeyError(assertion_id)

@view_config(route_name='objects.generic.traversal',
			 renderer='rest',
			 request_method='GET',
			 context=IBadgeAssertion)
class OpenAssertionView(object):

	def __init__(self, request):
		self.request = request

	def __call__(self):
		result = self.request.context
		return result

def get_badge_image_content(badge_url):
	__traceback_info__ = badge_url
	res = requests.get(badge_url)
	if res.status_code != 200:
		raise hexc.HTTPNotFound(_("Could not find badge image."))
	return res.content

def _copy_external(external):
	def _m(ext):
		if isinstance(ext, Mapping):
			result = {}
			for key, value in ext.items():
				result[key] = _m(value)
		elif isinstance(ext, (tuple, list)):
			result = []
			for value in ext:
				result.append(_m(value))
		else:
			result = ext
		return result
	result = _m(external)
	return result
	
def _produce_payload(external):
	external.pop('href', None)
	def _m(ext):
		if isinstance(ext, Mapping):
			for key in ALL:
				ext.pop(key, None)
			for key, value in ext.items():
				if value is None:
					ext.pop(key, None)
				else:
					_m(value)
		elif isinstance(ext, (tuple, list)):
			for value in ext:
				_m(value)
	_m(external)
	return external
		
class BaseOpenAssertionView(object):

	def _do_call(self):
		request = self.request
		badge = IBadgeClass(request.context)
		external = to_external_object(request.context)
		badge_url = get_badge_image_url(badge, request)
		return external, badge_url

class BaseAssertionImageView(AbstractAuthenticatedView, BaseOpenAssertionView):

	def _get_image(self, badge_url, payload=None, locked=False):
		content = get_badge_image_content(badge_url)
		target = source = BytesIO(content)
		source.seek(0)
		if locked:
			target = BytesIO()
			bake_badge(	source, target, 
						payload=payload, 
						url=(badge_url if not payload else None))
			target.seek(0)
		return target

@view_config(name="baked-image")
@view_config(name="image.png")
@view_defaults(	route_name='objects.generic.traversal',
			 	request_method='GET',
				context=IBadgeAssertion,
			 	permission=nauth.ACT_READ)
class OpenAssertionImageView(BaseAssertionImageView):

	def __call__(self):
		external, badge_url = self._do_call()
		locked = is_locked(self.request.context)
		payload = _produce_payload(external) if is_locked else None
		target = self._get_image(badge_url, payload=payload, locked=locked)
		response = self.request.response
		response.body_file = target
		response.content_type = b'image/png; charset=UTF-8'
		response.content_disposition = b'attachment; filename="image.png"'
		return response

def assert_assertion_exported(context, remoteUser=None):
	context = context
	if not is_locked(context):
		user = IUser(context, None)
		if user is None:
			raise hexc.HTTPUnprocessableEntity(_("Cannot find user for assertion."))
		if remoteUser is not None and remoteUser != user:
			raise hexc.HTTPForbidden()
		email = get_user_email(user)
		email_verified = is_email_verified(user)
		if not email or not email_verified:
			msg = _("Cannot export assertion to an unverified email.")
			raise hexc.HTTPUnprocessableEntity(msg)
		update_assertion(context.uid, email=email, exported=True)

@view_config(name="mozillabackpack")
@view_config(name="assertion.json")
@view_defaults(	route_name='objects.generic.traversal',
			 	request_method='GET',
			 	context=IBadgeAssertion)
class OpenAssertionJSONView(AbstractAuthenticatedView, BaseOpenAssertionView):

	def __call__(self):
		external, _ = self._do_call()
		external = _produce_payload(external)
		context = self.request.context
		assert_assertion_exported(context, self.remoteUser)	
		return external

@view_config(name="lock")
@view_config(name="export")
@view_defaults(	route_name='objects.generic.traversal',
			 	request_method='POST',
				context=IBadgeAssertion,
			 	permission=nauth.ACT_READ)
class ExportOpenAssertionView(BaseAssertionImageView):

	def __call__(self):
		external, badge_url = self._do_call()
		context = self.request.context
		assert_assertion_exported(context, self.remoteUser)	
		payload = _produce_payload(external)
		target = self._get_image(badge_url, payload=payload, locked=True)
		response = self.request.response
		response.body_file = target
		response.content_type = b'image/png; charset=UTF-8'
		response.content_disposition = b'attachment; filename="image.png"'
		return response
