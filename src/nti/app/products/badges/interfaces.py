#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

from zope import component
from zope import interface
from zope.interface.interface import taggedValue

from nti.appserver.workspaces.interfaces import IWorkspace

from nti.app.client_preferences.interfaces import TAG_EXTERNAL_PREFERENCE_GROUP

from nti.dataserver.interfaces import IZContained
from nti.dataserver.interfaces import IStreamChangeEvent

class IAssertionChange(IStreamChangeEvent, IZContained):
	"""
	Interface marker for an Assertion change
	"""

class IBadgeSettings(interface.Interface):
	"""
	The root of the settings tree for badges
	"""
	taggedValue(TAG_EXTERNAL_PREFERENCE_GROUP, 'write')

class IBadgesWorkspace(IWorkspace):
	"""
	A workspace containing data for badges.
	"""

class IPrincipalBadgeFilter(interface.Interface):
	"""
	define subscriber badge filter
	"""

	def allow_badge(user, badge):
		"""
		allow the specified badge
		"""

class IPrincipalErnableBadges(interface.Interface):
	"""
	subscriber for a ernable badges for a principal
	"""
	def iter_badges():
		pass

class IPrincipalEarnedBadgeFilter(interface.Interface):
	"""
	define subscriber badge earned filter
	"""

	def allow_badge(user, badge):
		"""
		allow the specified badge
		"""

class IPrincipalEarnableBadgeFilter(interface.Interface):
	"""
	define subscriber badge earnable filter
	"""

	def allow_badge(user, badge):
		"""
		allow the specified badge
		"""

class IOpenBadgeAdapter(interface.Interface):

	"""
	Utility to adapt an object to a :class:`nti.badges.openbadges.interfaces.IBadgeClass`
	"""

	def adapt(context):
		"""
		adpapt the specified context to a IBadgeClass
		"""

def get_principal_badge_filter(user):
	filters = component.subscribers((user,), IPrincipalBadgeFilter)
	filters = list(filters)
	def uber_filter(badge):
		return all((f.allow_badge(user, badge) for f in filters))
	return uber_filter

def get_principal_earned_badge_filter(user):
	filters = component.subscribers((user,), IPrincipalEarnedBadgeFilter)
	filters = list(filters)
	def uber_filter(badge):
		return all((f.allow_badge(user, badge) for f in filters))
	return uber_filter

def get_principal_earnable_badge_filter(user):
	filters = component.subscribers((user,), IPrincipalEarnableBadgeFilter)
	filters = list(filters)
	def uber_filter(badge):
		return all((f.allow_badge(user, badge) for f in filters))
	return uber_filter

from nti.dataserver.interfaces import make_stream_change_event_interface

SC_BADGE_EARNED = 'BadgeEarned'
IStreamChangeBadgeEarnedEvent = make_stream_change_event_interface(SC_BADGE_EARNED)[0]
