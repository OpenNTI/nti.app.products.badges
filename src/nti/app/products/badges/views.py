#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
import urllib
import requests
from io import BytesIO
from urlparse import urljoin
from urlparse import urlparse
from collections import Mapping

from zope import component
from zope import interface
from zope.container.contained import Contained
from zope.traversing.interfaces import IPathAdapter

from pyramid.view import view_config
from pyramid.interfaces import IRequest
from pyramid import httpexceptions as hexc

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.appserver.interfaces import IUserService

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

from .interfaces import IBadgesWorkspace

from . import OPEN_BADGES_VIEW
from . import HOSTED_BADGE_IMAGES
from . import OPEN_ASSERTIONS_VIEW

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

		raise hexc.HTTPNotFound('Badge not found')

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
			 context=OpenAssertionsPathAdapter)
class OpenAssertionView(object):

	def __init__(self, request):
		self.request = request

	def __call__(self):
		return self.request.context

def get_badge_image_content(badge_url):
	__traceback_info__ = badge_url
	res = requests.get(badge_url)
	if res.status_code != 200:
		raise hexc.HTTPNotFound("Could not find badge image")
	return res.content
		
class BaseOpenAssertionView(object):

	def __call__(self):
		request = self.request
		external = to_external_object(request.context)
		badge = external.get('badge')
		if isinstance(badge, six.string_types):
			badge_url = badge
		else:
			badge_url = badge.get('image')

		if not badge_url:
			raise hexc.HTTPNotFound("Badge url not found")

		p = urlparse(badge_url)
		if not p.scheme:
			## CS: Handle the case where the badge url is an image name.
			## make sure we complete with the correct path
			badge_url = "%s/%s" % (urljoin(request.host_url, HOSTED_BADGE_IMAGES), 
								   badge_url)
		
		return external, badge_url

@view_config(route_name='objects.generic.traversal',
			 request_method='GET',
			 context=IBadgeAssertion,
			 permission=nauth.ACT_READ,
			 name="image.png")
class OpenAssertionImageView(AbstractAuthenticatedView, BaseOpenAssertionView):

	def __call__(self):
		external, badge_url = super(OpenAssertionImageView, self).__call__()
		content = get_badge_image_content(badge_url)
		source = BytesIO(content)
		source.seek(0)
		
		url = urljoin(self.request.host_url, external['href'])
		target = BytesIO()
		bake_badge(source, target, url=url)
		target.seek(0)

		response = self.request.response
		response.body_file = target
		response.content_type = b'image/png; charset=UTF-8'
		response.content_disposition = b'attachment; filename="image.png"'
		return response

@view_config(route_name='objects.generic.traversal',
			 request_method='GET',
			 context=IBadgeAssertion,
			 name="assertion.json")
class OpenAssertionJSONView(BaseOpenAssertionView):

	def __init__(self, request):
		self.request = request

	def _clean(self, external):
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
	
	def __call__(self):
		external, _ = super(OpenAssertionJSONView, self).__call__()
		external = self._clean(external)
		return external
