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
from pyramid.response import Response as PyramidResponse

from nti.app.base.abstract_views import AbstractView
from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.renderers.interfaces import INoHrefInResponse

from nti.appserver.workspaces.interfaces import IUserService

from nti.badges.interfaces import IEarnedBadge
from nti.badges.interfaces import IBadgeManager
from nti.badges.openbadges.utils.badgebakery import bake_badge

from nti.badges.openbadges.interfaces import IBadgeClass
from nti.badges.openbadges.interfaces import IBadgeAssertion
from nti.badges.openbadges.interfaces import IIssuerOrganization

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
from . import OPEN_ISSUERS_VIEW
from . import OPEN_ASSERTIONS_VIEW

from . import is_locked
from . import get_badge
from . import get_issuer
from . import get_assertion
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
	result = to_external_object(context, name="mozillabackpack",
								decorate=False)
	return result
	
class OpenJSONView(AbstractView):
	
	def _set_environ(self):
		environ = self.request.environ
		environ['HTTP_X_REQUESTED_WITH'] = b'xmlhttprequest'

class Response(PyramidResponse):
	default_charset = None

### Issuers

@interface.implementer(IPathAdapter)
@component.adapter(IDataserverFolder, IRequest)
class OpenIssuersPathAdapter(Contained):

	def __init__(self, dataserver, request):
		self.__parent__ = dataserver
		self.__name__ = OPEN_ISSUERS_VIEW

	def __getitem__(self, issuer_id):
		if not issuer_id:
			raise hexc.HTTPNotFound()

		issuer_id = urllib.unquote(issuer_id)
		result = get_issuer(issuer_id)
		if result is not None:
			result = IIssuerOrganization(result)
			result. __acl__ = acl_from_aces(
								ace_allowing(EVERYONE_USER_NAME, nauth.ACT_READ))
			return result
		raise KeyError(issuer_id)

@view_config(route_name='objects.generic.traversal',
			 renderer='rest',
			 request_method='GET',
			 context=IIssuerOrganization)
class OpenIssuerView(AbstractView):

	def __call__(self):
		result = self.request.context
		return result
	
@view_config(name="mozillabackpack")
@view_config(name="issuer.json")
@view_defaults(	route_name='objects.generic.traversal',
				renderer='rest',
				request_method='GET',
				context=IIssuerOrganization)
class OpenIssuerJSONView(OpenJSONView):

	def __call__(self):
		self._set_environ()
		result = _to__mozilla_backpack(self.request.context)
		interface.alsoProvides(result, INoHrefInResponse)
		return result

### Badges

@interface.implementer(IPathAdapter)
@component.adapter(IDataserverFolder, IRequest)
class OpenBadgesPathAdapter(Contained):

	def __init__(self, dataserver, request):
		self.__parent__ = dataserver
		self.__name__ = OPEN_BADGES_VIEW

	def __getitem__(self, badge_id):
		if not badge_id:
			raise hexc.HTTPNotFound()

		badge_id = urllib.unquote(badge_id)
		result = get_badge(badge_id)
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
class OpenBadgeJSONView(OpenJSONView):

	def __call__(self):
		self._set_environ()
		result = _to__mozilla_backpack(self.request.context)
		interface.alsoProvides(result, INoHrefInResponse)
		return result
	
### Assertions

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
		response = Response()
		response.body_file = target
		response.content_type = b'image/png'
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
class OpenAssertionJSONView(OpenJSONView):

	def __call__(self):
		context = self.request.context
		if not is_locked(context):
			raise hexc.HTTPUnprocessableEntity(_("Assertion is not locked."))
		self._set_environ()
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
		owner = IUser(context, None)
		if owner != self.remoteUser:
			raise hexc.HTTPForbidden()
	
		## verify the assertion can be exported
		assert_assertion_exported(context, self.remoteUser)	
		payload = _to__mozilla_backpack(context)
		badge_url = _get_badge_image_url(context, self.request)
		target = _get_image(badge_url, payload=payload, locked=True)
		
		## return baked image
		response = Response()
		response.body_file = target
		response.content_type = b'image/png'
		response.content_disposition = b'attachment; filename="image.png"'
		return response

@view_config(name="lock")
@view_config(name="export")
@view_defaults(	route_name='objects.generic.traversal',
			 	request_method='POST',
				context=IBadgeClass,
			 	permission=nauth.ACT_READ)
class LockBadgeView(AbstractAuthenticatedView):

	def __call__(self):
		context = self.request.context	
		assertion  = get_assertion(self.remoteUser, context.name)
		if assertion is None:
			raise hexc.HTTPUnprocessableEntity(_("Cannot find user assertion."))
		
		## verify the assertion can be exported and export
		assert_assertion_exported(assertion, self.remoteUser)
		interface.alsoProvides(context, IEarnedBadge) ## see decorators
		return context
