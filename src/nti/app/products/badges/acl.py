#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.badges.openbadges.interfaces import IBadgeClass
from nti.badges.openbadges.interfaces import IBadgeAssertion
from nti.badges.openbadges.interfaces import IIssuerOrganization

from nti.dataserver.authorization import ACT_READ

from nti.dataserver.authorization_acl import ace_allowing
from nti.dataserver.authorization_acl import acl_from_aces

from nti.dataserver.interfaces import EVERYONE_USER_NAME

from nti.dataserver.interfaces import IACLProvider

from nti.property.property import LazyOnClass

@interface.implementer(IACLProvider)
class OpenMixinACLProvider(object):

	def __init__(self, context):
		self.context = context

	@LazyOnClass
	def __acl__(self):
		return acl_from_aces(ace_allowing(EVERYONE_USER_NAME, ACT_READ, type(self)))

@component.adapter(IBadgeClass)
class OpenBadgeACLProvider(OpenMixinACLProvider):
	pass

@component.adapter(IIssuerOrganization)
class OpenIssuerACLProvider(OpenMixinACLProvider):
	pass

@component.adapter(IBadgeAssertion)
class OpenAssertionACLProvider(OpenMixinACLProvider):
	pass
