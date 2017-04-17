#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from nti.badges.openbadges.interfaces import IBadgeAssertion

from nti.badges.tahrir.interfaces import IAssertion

from nti.badges.tahrir.wref import AssertionWeakRef


@component.adapter(IBadgeAssertion)
class OpenAssertionWeakRef(AssertionWeakRef):

    def __init__(self, assertion):
        AssertionWeakRef.__init__(self, IAssertion(assertion))

    def __call__(self, allow_cached=False):
        result = AssertionWeakRef.__call__(self, allow_cached)
        return IBadgeAssertion(result, None)
