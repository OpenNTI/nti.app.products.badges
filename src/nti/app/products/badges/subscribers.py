#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface
from zope.lifecycleevent.interfaces import IObjectRemovedEvent

from nti.badges import interfaces as badge_interfaces

from nti.dataserver import interfaces as nti_interfaces

from . import interfaces
from . import get_user_id
from . import get_user_badge_managers

@component.adapter(nti_interfaces.IUser)
@interface.implementer(interfaces.IPrincipalBadgeManager)
class _DefaultPrincipalBadgeManager(object):

    __slots__ = ('context',)

    def __init__(self, context):
        self.context = context

    @property
    def manager(self):
        result = component.getUtility(badge_interfaces.IBadgeManager)
        return result

@component.adapter(nti_interfaces.IUser, IObjectRemovedEvent)
def _user_deleted(user, event):
    uid = get_user_id(user)
    for manager in get_user_badge_managers(user):
        manager.delete_user(uid)
