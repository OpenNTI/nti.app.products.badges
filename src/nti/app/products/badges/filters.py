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

from nti.appserver.interfaces import ICreatableObjectFilter

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

@interface.implementer(ICreatableObjectFilter)
class _BadgesContentObjectFilter(object):

	PREFIX_1 = u'application/vnd.nextthought.badges'
	PREFIX_2 = u'application/vnd.nextthought.openbadges'

	def __init__(self, context=None):
		pass

	def filter_creatable_objects(self, terms):
		for name in list(terms):  # mutating
			if name.startswith(self.PREFIX_1) or name.startswith(self.PREFIX_2):
				terms.pop(name, None)
		return terms
