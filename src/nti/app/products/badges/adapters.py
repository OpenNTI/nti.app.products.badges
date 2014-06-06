#!/usr/bin/env python
# -*- coding: utf-8 -*
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

from nti.dataserver import interfaces as nti_interfaces
from nti.dataserver.users import interfaces as user_interfaces

from nti.badges.model import NTIPerson
from nti.badges import interfaces as badges_interfaces

from nti.badges.openbadges.model import IdentityObject
from nti.badges.openbadges import interfaces as open_interfaces

from nti.badges.tahrir import interfaces as tahrir_interfaces

from . import get_user_id

@interface.implementer(open_interfaces.IIdentityObject)
@component.adapter(nti_interfaces.IUser)
def user_to_identity_object(user):
	uid = get_user_id(user)
	result = IdentityObject(identity=uid,
							type=open_interfaces.ID_TYPE_EMAIL,
							hashed=False,
							salt=None)
	return result

def _set_common_person(user, person):
	uid = get_user_id(user)
	person.email = uid
	profile = user_interfaces.IUserProfile(user)
	person.bio = getattr(profile, 'about', None) or u''
	person.website = getattr(profile, 'home_page', None) or u''

@interface.implementer(tahrir_interfaces.IPerson)
@component.adapter(nti_interfaces.IUser)
def user_to_tahrir_person(user):
	result = Person()
	_set_common_person(user, result)
	result.nickname = user.username
	result.created_on = datetime.fromtimestamp(user.createdTime)
	return result

from nti.dataserver.users import User

@interface.implementer(nti_interfaces.IUser)
@component.adapter(tahrir_interfaces.IPerson)
def tahrir_person_to_user(person):
	# We have the strict dependency on using
	# username as 'email' for now
	return User.get_user(person.email)

@interface.implementer(badges_interfaces.INTIPerson)
@component.adapter(nti_interfaces.IUser)
def user_to_ntiperson(user):
	result = NTIPerson()
	_set_common_person(user, result)
	result.name = user.username
	result.createdTime = user.createdTime
	return result

from nti.app.pushnotifications.digest_email import AbstractClassifier

from .interfaces import IStreamChangeBadgeEarnedEvent

@component.adapter(IStreamChangeBadgeEarnedEvent)
class _AssertionChangeEventClassifier(AbstractClassifier):
	classification = 'assertion'
