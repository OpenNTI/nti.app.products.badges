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

@component.adapter(nti_interfaces.IUser, IObjectRemovedEvent)
def _user_deleted(user, event):
    pass
