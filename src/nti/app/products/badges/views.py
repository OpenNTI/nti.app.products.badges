#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pyramid views.

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface
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
from nti.dataserver import interfaces as nti_interfaces

from nti.utils import maps

from . import interfaces
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
			badge = params.get('badge', params.get('badge_name', params.get('badgeName')))

		if not badge:
			raise hexc.HTTPUnprocessableEntity('Badge not specified')

		for manager in get_user_badge_managers(user):
			result = manager.get_badge(badge)
			if result is not None:
				return badge_interfaces.IBadgeClass(result)

		raise hexc.HTTPNotFound('Badge not found')
