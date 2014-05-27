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

from nti.badges import interfaces as badge_interfaces

from nti.dataserver import interfaces as nti_interfaces

from . import interfaces

@component.adapter(nti_interfaces.IUser)
@interface.implementer(interfaces.IPrincipalBadgeManager)
class _DefaultPrincipalBadgeManager(object):

    __slots__ = ('context',)

    def __init__(self, context):
        self.context = context

    def iter_managers(self):
        result = []
        for _, manager in component.getUtilitiesFor(badge_interfaces.IBadgeManager):
            result.append(manager)
        return result
