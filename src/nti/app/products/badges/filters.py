#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.dataserver.interfaces import IUser

from .interfaces import IPrincipalBadgeFilter
from .interfaces import IPrincipalEarnedBadgeFilter
from .interfaces import IPrincipalEarnableBadgeFilter

@component.adapter(IUser)
@interface.implementer(IPrincipalBadgeFilter)
class _DefaultPrincipalBadgeFilter(object):

	__slots__ = ()

	def __init__(self, *args):
		pass

	def allow_badge(self, user, badge):
		return True

@component.adapter(IUser)
@interface.implementer(IPrincipalEarnedBadgeFilter)
class _DefaultPrincipalEarnedBadgeFilter(object):

	__slots__ = ()

	def __init__(self, *args):
		pass

	def allow_badge(self, user, badge):
		return True

@component.adapter(IUser)
@interface.implementer(IPrincipalEarnableBadgeFilter)
class _DefaultPrincipalEarnableBadgeFilter(object):

	__slots__ = ()

	def __init__(self, *args):
		pass

	def allow_badge(self, user, badge):
		return True
