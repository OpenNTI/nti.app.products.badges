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

from zope import component
from zope import interface
from zope.container.contained import Contained
from zope.traversing.interfaces import IPathAdapter

from pyramid.view import view_config
from pyramid.view import view_defaults
from pyramid.interfaces import IRequest
from pyramid import httpexceptions as hexc

from nti.app.base.abstract_views import AbstractView
from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.renderers.interfaces import INoHrefInResponse

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

from nti.externalization.externalization import to_external_object

from .utils import get_badge_image_url
from .interfaces import IBadgesWorkspace

from . import OPEN_BADGES_VIEW
from . import OPEN_ASSERTIONS_VIEW

from . import is_locked
from . import get_user_email
from . import update_assertion
from . import is_email_verified

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

def _to__mozilla_backpack(context):
	result = to_external_object(context, name="mozillabackpack")
	return result

@interface.implementer(IPathAdapter)
@component.adapter(IDataserverFolder, IRequest)
class OpenBadgesPathAdapter(Contained):

	def __init__(self, dataserver, request):
		self.__parent__ = dataserver
		self.__name__ = OPEN_BADGES_VIEW

	def __getitem__(self, badge_id):
		if not badge_id:
			raise hexc.HTTPNotFound()

		manager = component.getUtility(IBadgeManager)
		result = manager.get_badge(badge_id)
		if result is not None:
			result = IBadgeClass(result)
			result. __acl__ = acl_from_aces(
								ace_allowing(EVERYONE_USER_NAME, nauth.ACT_READ))
			return result
		raise KeyError(badge_id)

@view_config(route_name='objects.generic.traversal',
			 renderer='rest',
			 request_method='GET',
			 context=IBadgeClass)
class OpenBadgeView(AbstractView):

	def __call__(self):
		result = self.request.context
		return result

@view_config(name="mozillabackpack")
@view_config(name="badge.json")
@view_defaults(	route_name='objects.generic.traversal',
				renderer='rest',
				request_method='GET',
				context=IBadgeClass)
class OpenBadgeJSONView(OpenBadgeView):

	def __call__(self):
		result = _to__mozilla_backpack(self.request.context)
		interface.alsoProvides(result, INoHrefInResponse)
		return result
	
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
class OpenAssertionView(AbstractView):

	def __call__(self):
		result = self.request.context
		return result

def get_badge_image_content(badge_url):
	__traceback_info__ = badge_url
	res = requests.get(badge_url)
	if res.status_code != 200:
		raise hexc.HTTPNotFound(_("Could not find badge image."))
	return res.content

def _get_badge_image_url(context, request=None):
	badge = IBadgeClass(context)
	badge_url = get_badge_image_url(badge, request)
	return badge_url

def _get_image(badge_url, payload=None, locked=False):
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
				context=IBadgeAssertion)
class OpenAssertionImageView(AbstractView):

	def __call__(self):
		context = self.request.context
		
		## baked image if locked
		locked = is_locked(context)
		badge_url = _get_badge_image_url(context, self.request)
		payload = _to__mozilla_backpack(context) if is_locked else None
		target = _get_image(badge_url, payload=payload, locked=locked)
		
		## return baked image
		response = self.request.response
		response.body_file = target
		response.content_type = b'image/png; charset=UTF-8'
		response.content_disposition = b'attachment; filename="image.png"'
		return response

def assert_assertion_exported(context, remoteUser=None):
	context = context
	if is_locked(context):
		return

	## verify user access
	user = IUser(context, None)
	if user is None:
		raise hexc.HTTPUnprocessableEntity(_("Cannot find user for assertion."))
	if remoteUser is not None and remoteUser != user:
		raise hexc.HTTPForbidden()
	
	## cehck if email has been verified
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
class OpenAssertionJSONView(AbstractView):

	def __call__(self):
		context = self.request.context
		if not is_locked(context):
			raise hexc.HTTPUnprocessableEntity(_("Assertion is not locked"))
		external = _to__mozilla_backpack(context)
		interface.alsoProvides(external, INoHrefInResponse)
		return external

@view_config(name="lock")
@view_config(name="export")
@view_defaults(	route_name='objects.generic.traversal',
			 	request_method='POST',
				context=IBadgeAssertion,
			 	permission=nauth.ACT_READ)
class ExportOpenAssertionView(AbstractAuthenticatedView):

	def __call__(self):
		context = self.request.context
		
		## verify the assertion can be exported
		assert_assertion_exported(context, self.remoteUser)	
		payload = _to__mozilla_backpack(context)
		badge_url = _get_badge_image_url(context, self.request)
		target = _get_image(badge_url, payload=payload, locked=True)
		
		## return baked image
		response = self.request.response
		response.body_file = target
		response.content_type = b'image/png; charset=UTF-8'
		response.content_disposition = b'attachment; filename="image.png"'
		return response
