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

@component.adapter(nti_interfaces.IUser)
@interface.implementer(open_interfaces.IIdentityObject)
def user_to_identity_object(user):
    uid = get_user_id(user)
    result = IdentityObject(identity=uid,
                            type=open_interfaces.ID_TYPE_EMAIL,
                            hashed=False,
                            salt=None)
    return result

@component.adapter(nti_interfaces.IUser)
@interface.implementer(tahrir_interfaces.IPerson)
def user_to_tahrir_person(user):
    uid = get_user_id(user)
    profile = user_interfaces.IUserProfile(user)
    result = Person()
    result.email = uid
    result.nickname = user.username
    result.bio = getattr(profile, 'about', None) or u''
    result.website = getattr(profile, 'home_page', None) or u''
    result.created_on = datetime.fromtimestamp(user.createdTime)
    return result

@component.adapter(nti_interfaces.IUser)
@interface.implementer(badges_interfaces.INTIPerson)
def user_to_ntiperson(user):
    uid = get_user_id(user)
    result = NTIPerson()
    result.email = uid
    result.name = user.username
    result.createdTime = user.createdTime
    profile = user_interfaces.IUserProfile(user)
    result.bio = getattr(profile, 'about', None) or u''
    result.website = getattr(profile, 'home_page', None) or u''
    return result

