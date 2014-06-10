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
HOSTED_BADGE_IMAGES = 'hosted_badge_images'

from .utils import has_side_effects

def get_user_id(user):
	result = user.username  # TODO: Switch to email when they can be verified
	return result

# issuers

@has_side_effects
def issuer_exists(issuer):
	manager = component.getUtility(badge_interfaces.IBadgeManager)
	result = manager.issuer_exists(issuer)
	return result

def add_issuer(issuer):
	manager = component.getUtility(badge_interfaces.IBadgeManager)
	result = manager.add_issuer(issuer)
	return result

# badges

@has_side_effects
def badge_exists(badge):
	manager = component.getUtility(badge_interfaces.IBadgeManager)
	result = manager.badge_exists(badge)
	return result

def add_badge(badge, issuer):
	manager = component.getUtility(badge_interfaces.IBadgeManager)
	result = manager.add_badge(badge, issuer)
	return result

def update_badge(badge):
	manager = component.getUtility(badge_interfaces.IBadgeManager)
	result = manager.update_badge(badge)
	return result

@has_side_effects
def get_badge(badge):
	manager = component.getUtility(badge_interfaces.IBadgeManager)
	result = manager.get_badge(badge)
	return result

@has_side_effects
def get_all_badges():
	manager = component.getUtility(badge_interfaces.IBadgeManager)
	return manager.get_all_badges()

# persons

def add_person(person):
	manager = component.getUtility(badge_interfaces.IBadgeManager)
	return manager.add_person(person)

def delete_person(person):
	manager = component.getUtility(badge_interfaces.IBadgeManager)
	return manager.delete_person(person)

@has_side_effects
def person_exists(person):
	manager = component.getUtility(badge_interfaces.IBadgeManager)
	return manager.person_exists(person)

@has_side_effects
def get_person_badges(person):
	manager = component.getUtility(badge_interfaces.IBadgeManager)
	return manager.get_person_badges(person)

# assertions

def add_assertion(person, badge):
	manager = component.getUtility(badge_interfaces.IBadgeManager)
	return manager.add_assertion(person, badge)
	
def remove_assertion(person, badge):
	manager = component.getUtility(badge_interfaces.IBadgeManager)
	return manager.remove_assertion(person, badge)

@has_side_effects
def assertion_exists(user, badge):
	manager = component.getUtility(badge_interfaces.IBadgeManager)
	if manager.assertion_exists(user, badge):
		return True
	return False
