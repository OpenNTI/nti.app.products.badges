#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from nti.app.products.badges.interfaces import IPrincipalBadgeFilter
from nti.app.products.badges.interfaces import IPrincipalEarnedBadgeFilter
from nti.app.products.badges.interfaces import IPrincipalEarnableBadgeFilter

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import ICreatableObjectFilter

logger = __import__('logging').getLogger(__name__)


@component.adapter(IUser)
@interface.implementer(IPrincipalBadgeFilter)
class _DefaultPrincipalBadgeFilter(object):

    __slots__ = ()

    def __init__(self, *args):
        pass

    def allow_badge(self, unused_user, unused_badge):
        return True


@component.adapter(IUser)
@interface.implementer(IPrincipalEarnedBadgeFilter)
class _DefaultPrincipalEarnedBadgeFilter(object):

    __slots__ = ()

    def __init__(self, *args):
        pass

    def allow_badge(self, unused_user, unused_badge):
        return True


@component.adapter(IUser)
@interface.implementer(IPrincipalEarnableBadgeFilter)
class _DefaultPrincipalEarnableBadgeFilter(object):

    __slots__ = ()

    def __init__(self, *args):
        pass

    def allow_badge(self, unused_user, unused_badge):
        return True


@interface.implementer(ICreatableObjectFilter)
class _BadgesContentObjectFilter(object):

    PREFIX_1 = 'application/vnd.nextthought.badges'
    PREFIX_2 = 'application/vnd.nextthought.openbadges'

    def __init__(self, context=None):
        pass

    def filter_creatable_objects(self, terms):
        for name in tuple(terms):  # mutating
            if name.startswith(self.PREFIX_1) or name.startswith(self.PREFIX_2):
                terms.pop(name, None)
        return terms
