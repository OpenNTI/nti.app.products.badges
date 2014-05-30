#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from nti.badges import interfaces as badge_interfaces

from . import interfaces

BADGES = 'Badges'

def get_user_id(user):
	result = user.username  # TODO: Switch to email when they can be verified
	return result

def get_user_badge_managers(user):
	for pbm in component.subscribers((user,), interfaces.IPrincipalBadgeManager):
		for manager in pbm.iter_managers():
			yield manager

def get_badge(badge):
	for _, manager in component.getUtilitiesFor(badge_interfaces.IBadgeManager):
		result = manager.get_badge(badge)
		if result is not None:
			return result
	return None

def get_all_badges():
	for _, manager in component.getUtilitiesFor(badge_interfaces.IBadgeManager):
		for badge in manager.get_all_badges():
			yield badge

def assertion_exists(user, badge):
	for pbm in component.subscribers((user,), interfaces.IPrincipalBadgeManager):
		for manager in pbm.iter_managers():
			if manager.assertion_exists(user, badge):
				return True
	return False
