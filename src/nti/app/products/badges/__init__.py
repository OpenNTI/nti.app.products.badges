#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import zope.i18nmessageid
MessageFactory = zope.i18nmessageid.MessageFactory('nti.app.products.badges')

from zope import component

from nti.badges.interfaces import IBadgeManager

from nti.dataserver.users.interfaces import IUserProfile

#: Badges workspace
BADGES = 'Badges'

#: Issuers workspace
ISSUERS = 'Issuers'

#: Open badges views
OPEN_BADGES_VIEW = 'OpenBadges'

#: Open issuers views
OPEN_ISSUERS_VIEW = 'OpenIssuers'

#: Open assertions view
OPEN_ASSERTIONS_VIEW = 'OpenAssertions'

#: Hosted badges images directory name
HOSTED_BADGE_IMAGES = 'hosted_badge_images'


def get_user_id(user):
    profile = IUserProfile(user, None)
    if profile is not None and profile.email_verified:
        result = getattr(profile, 'email', None) or user.username
    else:
        result = user.username
    result = result.lower()
    return result


def get_user_email(user):
    profile = IUserProfile(user, None)
    try:
        return profile.email
    except AttributeError:
        return None


def is_email_verified(user):
    profile = IUserProfile(user, None)
    try:
        return profile.email_verified
    except AttributeError:
        return False

# issuers


def get_all_issuers():
    manager = component.queryUtility(IBadgeManager)
    return manager.get_all_issuers() if manager is not None else ()


def get_issuer(issuer):
    manager = component.queryUtility(IBadgeManager)
    return manager.get_issuer(issuer) if manager is not None else None


def issuer_exists(issuer):
    manager = component.getUtility(IBadgeManager)
    return manager.issuer_exists(issuer)


def add_issuer(issuer):
    manager = component.getUtility(IBadgeManager)
    return manager.add_issuer(issuer)

# badges


def badge_exists(badge):
    manager = component.getUtility(IBadgeManager)
    return manager.badge_exists(badge)


def add_badge(badge, issuer):
    manager = component.getUtility(IBadgeManager)
    return manager.add_badge(badge, issuer)


def update_badge(badge):
    manager = component.getUtility(IBadgeManager)
    return manager.update_badge(badge)


def get_badge(badge):
    manager = component.queryUtility(IBadgeManager)
    return manager.get_badge(badge) if manager is not None else None


def get_all_badges():
    manager = component.queryUtility(IBadgeManager)
    return manager.get_all_badges() if manager is not None else ()

# persons


def add_person(person):
    manager = component.getUtility(IBadgeManager)
    return manager.add_person(person)


def delete_person(person):
    manager = component.getUtility(IBadgeManager)
    return manager.delete_person(person)


def person_exists(person):
    manager = component.getUtility(IBadgeManager)
    return manager.person_exists(person)


def get_person_badges(person):
    manager = component.queryUtility(IBadgeManager)
    return manager.get_person_badges(person) if manager is not None else ()


def get_person_assertions(person):
    manager = component.queryUtility(IBadgeManager)
    return manager.get_person_assertions(person) if manager is not None else ()


def get_all_persons(person):
    manager = component.queryUtility(IBadgeManager)
    return manager.get_all_persons() if manager is not None else ()

# assertions


def add_assertion(person, badge, exported=False):
    manager = component.getUtility(IBadgeManager)
    return manager.add_assertion(person, badge, exported=exported)


def remove_assertion(person, badge):
    manager = component.getUtility(IBadgeManager)
    return manager.remove_assertion(person, badge)


def assertion_exists(user, badge):
    manager = component.getUtility(IBadgeManager)
    if manager.assertion_exists(user, badge):
        return True
    return False


def get_assertion(user, badge):
    manager = component.getUtility(IBadgeManager)
    return manager.get_assertion(user, badge)


def get_assertion_by_id(assertion_id):
    manager = component.getUtility(IBadgeManager)
    return manager.get_assertion_by_id(assertion_id)


def update_assertion(assertion_id, email=None, exported=True):
    manager = component.getUtility(IBadgeManager)
    return manager.update_assertion(assertion_id,
                                    email=email,
                                    exported=exported)


def is_locked(context):
    try:
        return context.exported
    except AttributeError:
        return False
is_exported = is_locked
