#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from datetime import datetime

from zope import component
from zope import interface

from tahrir_api.model import Person

from nti.dataserver.interfaces import IUser
from nti.dataserver.users.interfaces import IUserProfile

from nti.badges.model import NTIPerson
from nti.badges.interfaces import INTIPerson

from nti.badges.openbadges.model import IdentityObject
from nti.badges.openbadges.interfaces import IBadgeClass
from nti.badges.openbadges.interfaces import ID_TYPE_EMAIL
from nti.badges.openbadges.interfaces import IIdentityObject

from nti.badges.tahrir.interfaces import IPerson
from nti.badges.tahrir.interfaces import IAssertion

from . import get_user_id

@interface.implementer(IIdentityObject)
@component.adapter(IUser)
def user_to_identity_object(user):
	uid = get_user_id(user)
	result = IdentityObject(identity=uid,
							type=ID_TYPE_EMAIL,
							hashed=False,
							salt=None)
	return result

def set_common_person(user, person):
	uid = get_user_id(user)
	person.email = uid
	profile = IUserProfile(user, None)
	person.bio = getattr(profile, 'about', None) or u''
	person.website = getattr(profile, 'home_page', None) or u''

@interface.implementer(IPerson)
@component.adapter(IUser)
def user_to_tahrir_person(user):
	result = Person()
	set_common_person(user, result)
	result.nickname = user.username
	result.created_on = datetime.fromtimestamp(user.createdTime)
	return result

from nti.dataserver.users import User

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

@interface.implementer(IBadgeClass)
@component.adapter(IAssertion)
def tahrir_assertion_to_badge(assertion):
	return assertion.badge

@interface.implementer(INTIPerson)
@component.adapter(IUser)
def user_to_ntiperson(user):
	result = NTIPerson()
	result.name = user.username
	set_common_person(user, result)
	result.createdTime = user.createdTime
	return result

from nti.app.pushnotifications.digest_email import AbstractClassifier

from .interfaces import IStreamChangeBadgeEarnedEvent

@component.adapter(IStreamChangeBadgeEarnedEvent)
class _AssertionChangeEventClassifier(AbstractClassifier):
	classification = 'assertion'
