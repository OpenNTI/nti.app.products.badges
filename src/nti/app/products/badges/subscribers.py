#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import time

from zope import component
from zope.lifecycleevent.interfaces import IObjectCreatedEvent
from zope.lifecycleevent.interfaces import IObjectRemovedEvent

from nti.badges import interfaces as badges_interfaces

from nti.dataserver import interfaces as nti_interfaces

from . import get_user_badge_managers

@component.adapter(nti_interfaces.IUser, IObjectRemovedEvent)
def _user_deleted(user, event):
    person = badges_interfaces.INTIPerson(user)
    for manager in get_user_badge_managers(user):
        manager.delete_person(person)

@component.adapter(nti_interfaces.IUser, IObjectCreatedEvent)
def _user_created(user, event):
    ntiperson = badges_interfaces.INTIPerson(user)
    for manager in get_user_badge_managers(user):
        if not manager.person_exists(ntiperson):
            ntiperson.createdTime = time.time()
            manager.add_person(ntiperson)
