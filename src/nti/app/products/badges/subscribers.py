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

from nti.badges import interfaces as badges_interfaces
from nti.badges.tahrir import interfaces as tahrir_interfaces

from nti.dataserver import interfaces as nti_interfaces

from nti.processlifetime import IAfterDatabaseOpenedEvent

from . import get_user_badge_managers

@component.adapter(nti_interfaces.IUser, IObjectRemovedEvent)
def _user_deleted(user, event):
    person = badges_interfaces.INTIPerson(user)
    for manager in get_user_badge_managers(user):
        manager.delete_person(person)

@component.adapter(IAfterDatabaseOpenedEvent)
def _after_database_opened_listener(event):
    import transaction
    with transaction.manager:
        for _, manager in component.getUtilitiesFor(tahrir_interfaces.ITahrirBadgeManager):
            for _, issuer in component.getUtilitiesFor(tahrir_interfaces.IIssuer):
                manager.add_issuer(issuer)
            
