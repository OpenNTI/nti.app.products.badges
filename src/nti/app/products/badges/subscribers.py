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

from nti.dataserver import interfaces as nti_interfaces

from nti.badges import interfaces as badge_interfaces

from . import interfaces
from . import get_user_id
from . import get_badge_manager

@component.adapter(nti_interfaces.IUser)
@interface.implementer(interfaces.IPrincipalBadgeManagerCatalog)
class _DefaultPrincipalBadgeManager(object):

    def __init__(self, context):
        self.context = context

    def iter_managers(self):
        for manager in component.getUtilitiesFor(badge_interfaces.IBadgeManager):
            yield manager

@component.adapter(nti_interfaces.IUser, IObjectRemovedEvent)
def _user_deleted(user, event):
    uid = get_user_id(user)
    manager = get_badge_manager()
    if manager and manager.delete_user(uid):
        logger.info("User removed from badge manager")
