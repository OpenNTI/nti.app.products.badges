#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface
from zope.catalog.interfaces import ICatalog
from zope.location.interfaces import IContained
from zope.container import contained as zcontained
from zope.traversing.interfaces import IPathAdapter

from pyramid.view import view_config
from pyramid.interfaces import IRequest
from pyramid import httpexceptions as hexc

from nti.appserver.interfaces import IUserService

from nti.badges.openbadges import interfaces as badge_interfaces

from nti.dataserver.users import User
from nti.dataserver import authorization as nauth
from nti.dataserver.users import index as user_index
from nti.dataserver import interfaces as nti_interfaces

from nti.externalization.interfaces import LocatedExternalDict

from nti.utils import maps

from . import interfaces
from . import get_all_badges
from . import get_user_badge_managers

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

OPEN_BADGES_VIEW = 'OpenBadges'

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
		username = request.authenticated_userid
		user = User.get_user(username)
		
		splits = request.path_info.split('/')
		if splits[-1] != OPEN_BADGES_VIEW:
			badge = splits[-1]
		else:
			params = maps.CaseInsensitiveDict(request.params)
			badge = params.get('badge') or params.get('badge_name') or \
					params.get('badgeName')

		if not badge:
			raise hexc.HTTPUnprocessableEntity('Badge not specified')

		for manager in get_user_badge_managers(user):
			result = manager.get_badge(badge)
			if result is not None:
				return badge_interfaces.IBadgeClass(result)

		raise hexc.HTTPNotFound('Badge not found')

OPEN_ASSERTIONS_VIEW = 'OpenAssertions'

@view_config(route_name='objects.generic.traversal',
			 name=OPEN_ASSERTIONS_VIEW,
			 renderer='rest',
			 request_method='GET',
			 context=nti_interfaces.IDataserverFolder,
			 permission=nauth.ACT_READ)
class OpenAssertionsView(object):

	def __init__(self, request):
		self.request = request

	def __call__(self):
		request = self.request
		params = maps.CaseInsensitiveDict(request.params)
		username = params.get('user') or params.get('username') or params.get('email')
		badge = params.get('badge') or params.get('badge_name') or params.get('badgeName')

		user = User.get_user(username)
		if user is None:
			ent_catalog = component.getUtility(ICatalog, name=user_index.CATALOG_NAME)
			results = list(ent_catalog.searchResults(email=(username, username)))
			user = results[0] if results else None
		if user is None:
			raise hexc.HTTPNotFound('User not found')

		for manager in get_user_badge_managers(user):
			result = manager.get_assertion(user, badge)
			if result is not None:
				return badge_interfaces.IBadgeAssertion(result)

		raise hexc.HTTPNotFound('Assertion not found')


ALL_BADGES_VIEW = 'AllBadges'

@view_config(route_name='objects.generic.traversal',
			 name=ALL_BADGES_VIEW,
			 renderer='rest',
			 request_method='GET',
			 context=nti_interfaces.IDataserverFolder,
			 permission=nauth.ACT_MODERATE)
class AllBadgedView(object):

	def __init__(self, request):
		self.request = request

	def __call__(self):
		result = LocatedExternalDict()
		result['Items'] = items = []
		items.extend(badge_interfaces.IBadgeClass(x) for x in get_all_badges())
		return result
