#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six

from datetime import datetime

from zope import component
from zope import interface

from tahrir_api.model import Person

from nti.app.products.badges import get_user_id
from nti.app.products.badges import get_assertion_by_id

from nti.app.products.badges.interfaces import IStreamChangeBadgeEarnedEvent

from nti.app.pushnotifications.digest_email import AbstractClassifier

from nti.badges.interfaces import INTIPerson

from nti.badges.model import NTIPerson

from nti.badges.openbadges.interfaces import ID_TYPE_EMAIL

from nti.badges.openbadges.interfaces import IBadgeClass
from nti.badges.openbadges.interfaces import IBadgeAssertion
from nti.badges.openbadges.interfaces import IIdentityObject

from nti.badges.openbadges.model import IdentityObject

from nti.badges.tahrir.interfaces import IPerson
from nti.badges.tahrir.interfaces import IAssertion

from nti.contentfragments.interfaces import IPlainTextContentFragment

from nti.dataserver.interfaces import IUser

from nti.dataserver.users.interfaces import IUserProfile

from nti.dataserver.users.users import User


@interface.implementer(IIdentityObject)
@component.adapter(IUser)
def user_to_identity_object(user):
    uid = get_user_id(user)
    result = IdentityObject(identity=uid,
                            type=ID_TYPE_EMAIL,
                            hashed=False,
                            salt=None)
    return result


def to_plain_text(content):
    text = component.getAdapter(content,
                                IPlainTextContentFragment,
                                name='text')
    return text


def set_common_person(user, person):
    uid = get_user_id(user)
    person.email = uid
    profile = IUserProfile(user, None)
    person.website = getattr(profile, 'home_page', None) or u''
    about = getattr(profile, 'about', u'') or u''
    about = [about] if isinstance(about, six.string_types) else about
    about = to_plain_text(u' '.join(about))
    # Tahrir limit
    person.bio = about[:140]


@interface.implementer(IPerson)
@component.adapter(IUser)
def user_to_tahrir_person(user):
    result = Person()
    set_common_person(user, result)
    result.nickname = user.username
    result.created_on = datetime.fromtimestamp(user.createdTime)
    return result


@interface.implementer(IUser)
@component.adapter(IPerson)
def tahrir_person_to_user(person):
    __traceback_info__ = person.nickname, person.email
    result = User.get_user(person.nickname)
    return result


@interface.implementer(IUser)
@component.adapter(IAssertion)
def tahrir_assertion_to_user(assertion):
    return IUser(assertion.person)


@interface.implementer(IAssertion)
@component.adapter(IBadgeAssertion)
def open_assertion_to_tahrir_assertion(assertion):
    return get_assertion_by_id(assertion.uid)


@interface.implementer(IUser)
@component.adapter(IBadgeAssertion)
def open_assertion_to_user(assertion):
    assertion = IAssertion(assertion)
    return IUser(assertion.person)


@interface.implementer(IBadgeClass)
@component.adapter(IBadgeAssertion)
def open_assertion_to_badge(assertion):
    return assertion.badge


@interface.implementer(INTIPerson)
@component.adapter(IUser)
def user_to_ntiperson(user):
    result = NTIPerson()
    result.name = user.username
    set_common_person(user, result)
    result.createdTime = user.createdTime
    return result


@component.adapter(IStreamChangeBadgeEarnedEvent)
class _AssertionChangeEventClassifier(AbstractClassifier):
    classification = 'assertion'
