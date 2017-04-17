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

from zope.lifecycleevent.interfaces import IObjectRemovedEvent

import sqlalchemy.exc

from nti.app.products.badges import person_exists
from nti.app.products.badges import delete_person

from nti.app.products.badges.utils import get_badge_image_url

from nti.badges.interfaces import IBadgeManager
from nti.badges.interfaces import IBadgeAssertion

from nti.badges.openbadges.interfaces import IBadgeClass

from nti.badges.tahrir.interfaces import IIssuer

from nti.dataserver.interfaces import IUser 

from nti.processlifetime import IApplicationTransactionOpenedEvent


@component.adapter(IUser, IObjectRemovedEvent)
def _user_deleted(user, event):
    if person_exists(user):
        logger.info("Removing badge data for user %s", user)
        delete_person(user)


@component.adapter(IApplicationTransactionOpenedEvent)
def _after_database_opened_listener(event):
    logger.info("Adding registered tahrir issuers")

    # TODO: Should probably defer this until needed
    manager = component.queryUtility(IBadgeManager)
    if manager is None or getattr(manager, '_v_installed', False):
        return

    issuers = {x[1] for x in component.getUtilitiesFor(IIssuer)}

    setattr(manager, str('_v_installed'), True)
    for issuer in issuers:
        # FIXME: Under some circumstances, we can get an
        # IntegrityError: ConstraintViolation, even though
        # this code path only checks name and origin (even on the exists call!).
        # So clearly there's some sort of race condition here.
        # Is our transaction not actually isolated? Or at the wrong level?
        try:
            if not manager.issuer_exists(issuer):
                manager.add_issuer(issuer)
                logger.debug("Issuer (%s,%s) added",
                             issuer.name, issuer.origin)
        except (sqlalchemy.exc.IntegrityError, sqlalchemy.exc.InvalidRequestError):
            logger.warn("Integrity error", exc_info=True)


from nti.app.authentication import get_remote_user

from nti.app.notabledata.interfaces import IUserNotableDataStorage

from nti.app.products.badges.interfaces import SC_BADGE_EARNED
from nti.app.products.badges.interfaces import IAssertionChange

from nti.appserver.interfaces import IUserActivityStorage

from nti.badges.openbadges.interfaces import IBadgeAwardedEvent

from nti.dataserver.activitystream_change import Change

from nti.dataserver.authorization import ACT_READ

from nti.dataserver.authorization_acl import ace_allowing
from nti.dataserver.authorization_acl import acl_from_aces

from nti.dataserver.interfaces import ALL_PERMISSIONS

from nti.dataserver.interfaces import ACE_DENY_ALL

from nti.property.property import Lazy


@interface.implementer(IAssertionChange)
class AssertionChange(Change):
    """
    Gives some class-level defaults that are useful
    for assertions/badges.
    """
    image = None

    # When we write this out, turn the assertion into the actual
    # badge
    def externalObjectTransformationHook(self, assertion):
        return IBadgeClass(assertion)

    # for ease of rendering
    @Lazy
    def badge(self):
        obj = self.object
        if obj is not None:
            badge = self.externalObjectTransformationHook(obj)
            return badge

    @Lazy
    def badge_href(self):
        return self.image or self.badge.image

    @Lazy
    def badge_description(self):
        return self.badge.description

    @Lazy
    def recipient(self):
        return IUser(self.object, None)
    
    # Eventually the assertion will have its own ACL,
    # we want to use that. Right now it has no provider,
    # so it gets no value from the superclass...
    __copy_object_acl__ = True

    # ...but we override to deny access for everyone except the
    # "creator", which right now is the owner of the
    # assertion...notable data bypasses this check for us
    @Lazy
    def __acl__(self):
        aces = []
        creator = self.creator
        if creator is not None:
            aces.add(ace_allowing(creator, ALL_PERMISSIONS))
        recipient = self.recipient
        if recipient is not None:
            aces.add(ace_allowing(recipient, ACT_READ))
        aces.append(ACE_DENY_ALL)
        return acl_from_aces(aces)


@component.adapter(IBadgeAssertion, IBadgeAwardedEvent)
def _make_assertions_notable_to_target(assertion, event):
    """
    When a badge assertion is recorded, the event is notable
    for the target user.
    """
    change = AssertionChange(SC_BADGE_EARNED, assertion)

    # set badge image
    badge = IBadgeClass(assertion)
    image = get_badge_image_url(badge)
    change.image = image if image else None

    user = IUser(assertion)
    # Set a creator...this may not be the best we can do in some cases
    change.creator = get_remote_user() or user

    storage = IUserNotableDataStorage(user)
    storage.store_object(change, safe=True, take_ownership=True)

    # At this point we can now put it in the default container in the
    # intid-based activity stream for the user...pending ACL work. To
    # be able to do that smoothly, we define a subclass of Change so
    # we can easily toggle the values.
    act_storage = IUserActivityStorage(user, None)
    if act_storage is not None:
        act_storage.addContainedObjectToContainer(change, '')
