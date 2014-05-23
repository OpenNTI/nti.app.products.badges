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

from pyramid.interfaces import IRequest
from pyramid.threadlocal import get_current_request

from nti.appserver.interfaces import IUserService

from nti.dataserver.users import User
from nti.dataserver import interfaces as nti_interfaces

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

@interface.implementer(IPathAdapter)
@component.adapter(nti_interfaces.IDataserverFolder, IRequest)
class OpenBadgesPathAdapter(zcontained.Contained):

    def __init__(self, course, request):
        self.__parent__ = course
        self.__name__ = 'OpenBadges'

    def __getitem__(self, badge):
        request = get_current_request()
        username = request.authenticated_userid if request else None
        user = User.get_user(username) if username else None
        if user is not None:
            for manager in get_user_badge_managers(user):
                result = manager.get_badge(badge)
                if result is not None:
                    return result
        raise KeyError(badge)
