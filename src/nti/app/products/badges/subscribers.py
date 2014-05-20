#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope.lifecycleevent.interfaces import IObjectRemovedEvent

from nti.dataserver import interfaces as nti_interfaces

from . import get_user_email
from . import get_badge_manager

@component.adapter(nti_interfaces.IUser, IObjectRemovedEvent)
def _user_deleted(user, event):
    email = get_user_email(user)
    manager = get_badge_manager()
    if manager and email and manager.delete_user(email):
        logger.info("User removed from badge manager")


