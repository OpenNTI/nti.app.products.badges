#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.dataserver import interfaces as nti_interfaces
from nti.dataserver.users import interfaces as user_interfaces

from . import openbadges
from . import interfaces as badge_interfaces

@component.adapter(nti_interfaces.IUser)
@interface.implementer(badge_interfaces.IIdentityObject)
def user_to_identity_object(user):
    profile = user_interfaces.IUserProfile(user)
    email = getattr(profile, 'email', None)
    if not email:
        raise TypeError("no user email found")
    result = openbadges.IdentityObject(identity=email,
                                       type=badge_interfaces.ID_TYPE_EMAIL,
                                       hashed=False,
                                       salt=None)
    return result
