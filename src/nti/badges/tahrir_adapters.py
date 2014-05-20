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

from . import tahrir_interfaces

@component.adapter(nti_interfaces.IUser)
@interface.implementer(tahrir_interfaces.IPerson)
def user_to_tahrir_person(user):
    profile = user_interfaces.IUserProfile(user)
    email = getattr(profile, 'email', None)
    if not email:
        raise TypeError("no user email found")
    result = Person()
    result.email = email
    result.nickname = getattr(profile, 'alias', None) or \
                      getattr(profile, 'realname', None) or \
                      user.username
    result.website = getattr(profile, 'home_page', None) or u''
    result.bio = getattr(profile, 'about', None) or u''
    result.created_on = datetime.fromtimestamp(user.createdTime)
    return result
