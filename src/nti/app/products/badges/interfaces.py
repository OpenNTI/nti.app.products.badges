#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=inherit-non-class

from zope import component
from zope import interface

from zope.interface.interface import taggedValue

from zope.location.interfaces import IContained

from zope.security.permission import Permission

from nti.appserver.workspaces.interfaces import IWorkspace

from nti.app.client_preferences.interfaces import TAG_EXTERNAL_PREFERENCE_GROUP

from nti.dataserver.interfaces import IStreamChangeEvent
from nti.dataserver.interfaces import make_stream_change_event_interface

#: Award a badge permission
ACT_AWARD_BADGE = Permission('nti.actions.badges.award')


class IAssertionChange(IStreamChangeEvent, IContained):
    """
    Interface marker for an Assertion change
    """


class IBadgeSettings(interface.Interface):
    """
    The root of the settings tree for badges
    """
    taggedValue(TAG_EXTERNAL_PREFERENCE_GROUP, 'write')


class IBadgesWorkspace(IWorkspace):
    """
    A workspace containing data for badges.
    """


class IPrincipalBadgeFilter(interface.Interface):
    """
    define subscriber badge filter
    """

    def allow_badge(user, badge):
        """
        allow the specified badge
        """


class IPrincipalErnableBadges(interface.Interface):
    """
    subscriber for a ernable badges for a principal
    """
    def iter_badges():
        pass


class IPrincipalEarnedBadgeFilter(interface.Interface):
    """
    define subscriber badge earned filter
    """

    def allow_badge(user, badge):
        """
        allow the specified badge
        """


class IPrincipalEarnableBadgeFilter(interface.Interface):
    """
    define subscriber badge earnable filter
    """

    def allow_badge(user, badge):
        """
        allow the specified badge
        """


class IOpenBadgeAdapter(interface.Interface):

    """
    Utility to adapt an object to a :class:`nti.badges.openbadges.interfaces.IBadgeClass`
    """

    def adapt(context):
        """
        adpapt the specified context to a IBadgeClass
        """


def get_principal_badge_filter(user):
    filters = component.subscribers((user,), IPrincipalBadgeFilter)
    filters = list(filters)
    def uber_filter(badge):
        return all((f.allow_badge(user, badge) for f in filters))
    return uber_filter


def get_principal_earned_badge_filter(user):
    filters = component.subscribers((user,), IPrincipalEarnedBadgeFilter)
    filters = list(filters)
    def uber_filter(badge):
        return all((f.allow_badge(user, badge) for f in filters))
    return uber_filter


def get_principal_earnable_badge_filter(user):
    filters = component.subscribers((user,), IPrincipalEarnableBadgeFilter)
    filters = list(filters)
    def uber_filter(badge):
        return all((f.allow_badge(user, badge) for f in filters))
    return uber_filter

#: Badge Earned Stream Change
SC_BADGE_EARNED = u'BadgeEarned'
IStreamChangeBadgeEarnedEvent = make_stream_change_event_interface(SC_BADGE_EARNED)[0]
