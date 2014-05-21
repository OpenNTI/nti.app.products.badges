#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from . import interfaces

def get_user_id(user):
	result = user.username  # TODO: Switch to email when they can be verified
	return result

def get_user_badge_managers(user):
	for manager in component.subscribers((user,), interfaces.IPrincipalBadgeManager):
		yield manager
