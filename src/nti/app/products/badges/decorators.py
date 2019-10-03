#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from collections import Mapping

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

from nti.appserver.pyramid_authorization import has_permission

from nti.badges.interfaces import IBadgeClass
from nti.badges.interfaces import IBadgeManager
from nti.badges.interfaces import IEarnedBadge
from nti.badges.interfaces import IBadgeAssertion

from nti.badges.openbadges.interfaces import IBadgeAssertion as IOpenAssertion

from nti.dataserver.authorization import ACT_READ

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

    def _do_decorate_external(self, context, mapping):  # pylint: disable=arguments-differ
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

    def _do_decorate_external(self, context, mapping):  # pylint: disable=arguments-differ
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

    def _predicate(self, context, unused_result):
        return component.queryUtility(IBadgeManager) is not None \
            and has_permission(ACT_READ, context)

    def _do_decorate_external(self, context, mapping):  # pylint: disable=arguments-differ
        _links = mapping.setdefault(LINKS, [])
        _links.append(Link(context, elements=(BADGES,), rel=BADGES))


@component.adapter(IUser)
@interface.implementer(IExternalObjectDecorator)
class BadgesRelRemoverDecorator(Singleton):
    """
    Decorator that can be registered to remove the badges rel, if necessary
    """

    def decorateExternalObject(self, unused_context, mapping):
        new_links = []
        _links = mapping.setdefault(LINKS, [])
        for link in _links:
            try:
                # Some links may be externalized already.
                if isinstance(link, Mapping):
                    rel = link.get('rel')
                else:
                    rel = link.rel
                if rel not in (BADGES,):
                    new_links.append(link)
            except AttributeError:
                pass
        mapping[LINKS] = new_links
