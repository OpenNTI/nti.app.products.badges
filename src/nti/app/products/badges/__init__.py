#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from nti.badges.interfaces import IBadgeManager

BADGES = 'Badges'
OPEN_BADGES_VIEW = 'OpenBadges'
OPEN_ASSERTIONS_VIEW = 'OpenAssertions'
HOSTED_BADGE_IMAGES = 'hosted_badge_images'

def get_user_id(user):
	result = user.username  # TODO: Switch to email when they can be verified
	return result

# issuers

def issuer_exists(issuer):
	manager = component.getUtility(IBadgeManager)
	result = manager.issuer_exists(issuer)
	return result

def add_issuer(issuer):
	manager = component.getUtility(IBadgeManager)
	result = manager.add_issuer(issuer)
	return result

# badges

def badge_exists(badge):
	manager = component.getUtility(IBadgeManager)
	result = manager.badge_exists(badge)
	return result

def add_badge(badge, issuer):
	manager = component.getUtility(IBadgeManager)
	result = manager.add_badge(badge, issuer)
	return result

def update_badge(badge):
	manager = component.getUtility(IBadgeManager)
	result = manager.update_badge(badge)
	return result

def get_badge(badge):
	manager = component.getUtility(IBadgeManager)
	result = manager.get_badge(badge)
	return result

def get_all_badges():
	manager = component.getUtility(IBadgeManager)
	result = manager.get_all_badges()
	return result

# persons

def add_person(person):
	manager = component.getUtility(IBadgeManager)
	result = manager.add_person(person)
	return result

def delete_person(person):
	manager = component.getUtility(IBadgeManager)
	result = manager.delete_person(person)
	return result

def person_exists(person):
	manager = component.getUtility(IBadgeManager)
	result = manager.person_exists(person)
	return result

def get_person_badges(person):
	manager = component.getUtility(IBadgeManager)
	result = manager.get_person_badges(person)
	return result

def get_person_assertions(person):
	manager = component.getUtility(IBadgeManager)
	result = manager.get_person_assertions(person)
	return result

# assertions

def add_assertion(person, badge):
	manager = component.getUtility(IBadgeManager)
	result = manager.add_assertion(person, badge)
	return result
	
def remove_assertion(person, badge):
	manager = component.getUtility(IBadgeManager)
	result = manager.remove_assertion(person, badge)
	return result

def assertion_exists(user, badge):
	manager = component.getUtility(IBadgeManager)
	if manager.assertion_exists(user, badge):
		return True
	return False

def get_assertion(user, badge):
	manager = component.getUtility(IBadgeManager)
	result = manager.get_assertion(user, badge)
	return result

