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

from nti.dataserver import interfaces as nti_interfaces

from . import interfaces

@component.adapter(nti_interfaces.IUser)
@interface.implementer(interfaces.IPrincipalBadgeFilter)
class _DefaultPrincipalBadgeFilter(object):

    __slots__ = ()

    def __init__(self, *args):
        pass

    def allow_badge(self, badge, user):
        return True

