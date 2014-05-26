#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

from zope import component
from zope import interface

from nti.appserver import interfaces as app_interfaces

class IBadgesWorkspace(app_interfaces.IWorkspace):
	"""
	A workspace containing data for badges.
	"""

class IPrincipalBadgeManager(interface.Interface):
	
	def iter_managers():
		"""
		Return an iterable of IBadgeManager objects
		"""

class IPrincipalBadgeFilter(interface.Interface):
	"""
	define subscriber badge filter
	"""

	def allow_badge(badge, user):
		"""
		allow the specified badge
		"""

class IPrincipalErnableBadges(interface.Interface):
	"""
	subscriber for a ernable badges for a principal
	"""
	def iter_badges():
		pass

def get_badge_predicate_for_user(user):
	filters = component.subscribers((user,), IPrincipalBadgeFilter)
	filters = list(filters)
	def uber_filter(badge):
		return all((f.allow_badge(badge, user) for f in filters))
	return uber_filter
