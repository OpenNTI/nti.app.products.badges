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

from nti.app.products.badges import BADGES
from nti.app.products.badges import is_locked
from nti.app.products.badges import get_assertion

from nti.app.products.badges.utils import get_badge_href
from nti.app.products.badges.utils import get_assertion_href
from nti.app.products.badges.utils import get_badge_image_url
from nti.app.products.badges.utils import get_assertion_json_url
from nti.app.products.badges.utils import get_assertion_image_url

from nti.app.renderers.decorators import AbstractAuthenticatedRequestAwareDecorator

from nti.badges.interfaces import IBadgeClass
from nti.badges.interfaces import IEarnedBadge
from nti.badges.interfaces import IBadgeAssertion

from nti.badges.openbadges.interfaces import IBadgeAssertion as IOpenAssertion

from nti.dataserver.interfaces import IUser

from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IExternalObjectDecorator
from nti.externalization.interfaces import IExternalMappingDecorator

from nti.externalization.singleton import Singleton

from nti.links.links import Link

LINKS = StandardExternalFields.LINKS

logger = __import__('logging').getLogger(__name__)


def _assertion_links(links, context, remoteUser, request, badge=None):
    owner = IUser(context, None)
    if owner != remoteUser:
        return
    locked = is_locked(context)
    if locked:
        # add link to baked image
        href = get_assertion_image_url(context, request)
        links.append(Link(href, rel='baked-image'))
        # add link to assertion json
        href = get_assertion_json_url(context, request)
        links.append(Link(href, rel='mozilla-backpack'))
    else:
        # add link to export/lock assertion
        if badge is None:
            href = get_assertion_href(context, request)
        else:
            href = get_badge_href(badge, request)
        links.append(Link(href, elements=('@@lock',), rel='lock'))
    return locked


def is_earned_badge(context, unused_user=None):
    return IEarnedBadge.providedBy(context)


@component.adapter(IBadgeClass)
@interface.implementer(IExternalMappingDecorator)
class _BadgeLinkFixer(AbstractAuthenticatedRequestAwareDecorator):

    def _do_decorate_external(self, context, mapping):
        request = self.request
        mapping['href'] = get_badge_href(context, request)
        mapping['image'] = get_badge_image_url(context, request)
        if is_earned_badge(context):  # test to avoid a lot of db ops
            assertion = get_assertion(self.remoteUser, context)
            if assertion is not None:
                _links = mapping.setdefault(LINKS, [])
                href = get_assertion_href(assertion, request)
                _links.append(Link(href, rel="assertion"))
                locked = _assertion_links(_links, assertion, self.remoteUser,
                                          request, badge=context)
                mapping['Locked'] = locked


@component.adapter(IBadgeAssertion)
@interface.implementer(IExternalMappingDecorator)
class _BadgeAssertionDecorator(AbstractAuthenticatedRequestAwareDecorator):

    def _do_decorate_external(self, context, mapping):
        request = self.request
        _links = mapping.setdefault(LINKS, [])
        mapping['href'] = get_assertion_href(context, request)
        mapping['image'] = get_assertion_image_url(context, request)
        locked = _assertion_links(_links, context, self.remoteUser, request)
        mapping['Locked'] = locked


@component.adapter(IOpenAssertion)
@interface.implementer(IExternalObjectDecorator)
class _OpenAssertionDecorator(Singleton):

    def decorateExternalObject(self, context, external):
        if not is_locked(context):
            external.pop('verify', None)


@component.adapter(IUser)
@interface.implementer(IExternalMappingDecorator)
class _UserBadgesLinkDecorator(AbstractAuthenticatedRequestAwareDecorator):

    def _do_decorate_external(self, context, mapping):
        _links = mapping.setdefault(LINKS, [])
        _links.append(Link(context, elements=(BADGES,), rel=BADGES))
