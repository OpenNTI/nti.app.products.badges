#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import urllib

from zope import component
from zope import interface
from zope.location.interfaces import IContained
from zope.container import contained as zcontained
from zope.traversing.interfaces import IPathAdapter

from pyramid.view import view_config
from pyramid.interfaces import IRequest
from pyramid import httpexceptions as hexc

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.appserver.interfaces import IUserService

from nti.badges import interfaces as badge_interfaces
from nti.badges.openbadges import interfaces as open_interfaces

from nti.dataserver import authorization as nauth
from nti.dataserver import interfaces as nti_interfaces
from nti.dataserver.authorization_acl import ace_allowing
from nti.dataserver.authorization_acl import acl_from_aces

from nti.externalization.interfaces import LocatedExternalDict

from . import interfaces
from . import get_all_badges
from . import OPEN_BADGES_VIEW
from . import OPEN_ASSERTIONS_VIEW

@interface.implementer(IPathAdapter)
@component.adapter(nti_interfaces.IUser, IRequest)
def BadgesWorkspacePathAdapter(context, request):
	service = IUserService(context)
	workspace = interfaces.IBadgesWorkspace(service)
	return workspace

@interface.implementer(IPathAdapter, IContained)
class BadgeAdminPathAdapter(zcontained.Contained):

	__name__ = 'BadgeAdmin'

	def __init__(self, context, request):
		self.context = context
		self.request = request
		self.__parent__ = context

@view_config(route_name='objects.generic.traversal',
			 name=OPEN_BADGES_VIEW,
			 renderer='rest',
			 request_method='GET',
			 context=nti_interfaces.IDataserverFolder,
			 permission=nauth.ACT_READ)
class OpenBadgeView(object):

	def __init__(self, request):
		self.request = request

	def __call__(self):
		request = self.request
		
		badge = request.subpath[0] if request.subpath else ''
		if not badge:
			raise hexc.HTTPNotFound()

		manager = component.getUtility(badge_interfaces.IBadgeManager)
		result = manager.get_badge(badge)
		if result is not None:
			return open_interfaces.IBadgeClass(result)

		raise hexc.HTTPNotFound('Badge not found')

@interface.implementer(IPathAdapter)
@component.adapter(nti_interfaces.IDataserverFolder, IRequest)
class OpenAssertionsPathAdapter(zcontained.Contained):

	def __init__(self, dataserver, request):
		self.__parent__ = dataserver
		self.__name__ = OPEN_ASSERTIONS_VIEW

	def __getitem__(self, assertion_id):
		if not assertion_id:
			raise KeyError(assertion_id)

		assertion_id = urllib.unquote(assertion_id)
		manager = component.getUtility(badge_interfaces.IBadgeManager)
		result = manager.get_assertion_by_id(assertion_id)
		if result is not None:
			result = open_interfaces.IBadgeAssertion(result)
			result. __acl__ = acl_from_aces(
								ace_allowing(nti_interfaces.AUTHENTICATED_GROUP_NAME,
											 nauth.ACT_READ))
			return result

		raise KeyError(assertion_id)

@view_config(route_name='objects.generic.traversal',
			 renderer='rest',
			 request_method='GET',
			 context=OpenAssertionsPathAdapter,
			 permission=nauth.ACT_READ)
class OpenAssertionsView(AbstractAuthenticatedView):

	def __call__(self):
		return self.request.context

ALL_BADGES_VIEW = 'AllBadges'

@view_config(route_name='objects.generic.traversal',
			 name=ALL_BADGES_VIEW,
			 renderer='rest',
			 request_method='GET',
			 context=nti_interfaces.IDataserverFolder,
			 permission=nauth.ACT_MODERATE)
class AllBadgesView(object):

	def __init__(self, request):
		self.request = request

	def __call__(self):
		result = LocatedExternalDict()
		result['Items'] = items = []
		items.extend(open_interfaces.IBadgeClass(x) for x in get_all_badges())
		return result
