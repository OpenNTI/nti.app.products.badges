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

from nti.badges import openbadges
from nti.badges import tahrir_interfaces
from nti.badges import interfaces as badge_interfaces

from . import get_user_email

@component.adapter(nti_interfaces.IUser)
@interface.implementer(badge_interfaces.IIdentityObject)
def user_to_identity_object(user):
    email = get_user_email(user)
    if not email:
        raise TypeError("no user email found")
    result = openbadges.IdentityObject(identity=email,
                                       type=badge_interfaces.ID_TYPE_EMAIL,
                                       hashed=False,
                                       salt=None)
    return result

@component.adapter(nti_interfaces.IUser)
@interface.implementer(tahrir_interfaces.IPerson)
def user_to_tahrir_person(user):
    email = get_user_email(user)
    if not email:
        raise TypeError("no user email found")
    profile = user_interfaces.IUserProfile(user)
    result = Person()
    result.email = email
    result.nickname = getattr(profile, 'alias', None) or \
                      getattr(profile, 'realname', None) or \
                      user.username
    result.website = getattr(profile, 'home_page', None) or u''
    result.bio = getattr(profile, 'about', None) or u''
    result.created_on = datetime.fromtimestamp(user.createdTime)
    return result

