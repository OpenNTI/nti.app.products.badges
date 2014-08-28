#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import collections

from zope import component
from zope import interface
from zope.lifecycleevent.interfaces import IAttributes
from zope.lifecycleevent.interfaces import IObjectRemovedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent

import sqlalchemy.exc

from nti.badges.interfaces import IBadgeManager
from nti.badges.interfaces import IBadgeAssertion

from nti.badges.tahrir.interfaces import IIssuer

from nti.dataserver import interfaces as nti_interfaces

from nti.processlifetime import IApplicationTransactionOpenedEvent

from . import person_exists
from . import delete_person

@component.adapter(nti_interfaces.IUser, IObjectRemovedEvent)
def _user_deleted(user, event):
	if person_exists(user):
		delete_person(user)

@component.adapter(nti_interfaces.IUser, IObjectModifiedEvent)
def _user_modified(user, event):
	if not person_exists(user):
		return

	descriptions = event.descriptions
	if descriptions and isinstance(descriptions, collections.Sequence):
		email_changed = False
		for desc in descriptions:
			if IAttributes.providedBy(desc) and 'email' in desc.attributes:
				email_changed = True
				break
		if email_changed:
			# TODO Update person
			pass

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
		except (sqlalchemy.exc.IntegrityError,sqlalchemy.exc.InvalidRequestError):
			logger.warn("Integrity error", exc_info=True)
		else:
			logger.debug("Issuer (%s,%s) added", issuer.name, issuer.origin)


from zope.lifecycleevent import IObjectAddedEvent

from nti.appserver.interfaces import IUserActivityStorage

from nti.app.notabledata.interfaces import IUserNotableDataStorage

from nti.badges.openbadges.interfaces import IBadgeClass

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import ACE_DENY_ALL
from nti.dataserver.activitystream_change import Change

from nti.dataserver.authorization import ACT_READ
from nti.dataserver.authorization_acl import ace_allowing
from nti.dataserver.authorization_acl import acl_from_aces

from .interfaces import SC_BADGE_EARNED, IAssertionChange

@interface.implementer(IAssertionChange)
class AssertionChange(Change):
	"""
	Gives some class-level defaults that are useful
	for assertions/badges.
	"""

	# When we write this out, turn the assertion into the actual
	# badge
	def externalObjectTransformationHook(self, assertion):
		return IBadgeClass(assertion)

	# for ease of rendering
	@property
	def badge(self):
		obj = self.object
		if obj is not None:
			badge = self.externalObjectTransformationHook(obj)
			return badge

	@property
	def badge_href(self):
		return self.badge.image

	@property
	def badge_description(self):
		return self.badge.description

	# Eventually the assertion will have its own ACL,
	# we want to use that. Right now it has no provider,
	# so it gets no value from the superclass...
	__copy_object_acl__ = True

	# ...but we override to deny access for everyone except the
	# "creator", which right now is the owner of the
	# assertion...notable data bypasses this check for us
	def __acl__(self):
		creator = self.creator
		if creator is not None:
			return acl_from_aces( ace_allowing( creator, ACT_READ ) )
		return (ACE_DENY_ALL,)

@component.adapter(IBadgeAssertion, IObjectAddedEvent)
def _make_assertions_notable_to_target(assertion, event):
	"""
	When a badge assertion is recorded, the event is notable
	for the target user.
	"""
	change = AssertionChange(SC_BADGE_EARNED, assertion)

	user = IUser(assertion)
	# Set a creator...this may not be the best we can do in some cases
	change.creator = user

	storage = IUserNotableDataStorage(user)
	storage.store_object(change, safe=True, take_ownership=True)

	# At this point we can now put it in the default container in the
	# intid-based activity stream for the user...pending ACL work. To
	# be able to do that smoothly, we define a subclass of Change so
	# we can easily toggle the values.
	act_storage = IUserActivityStorage(user, None)
	if act_storage is not None:
		act_storage.addContainedObjectToContainer(change, '')
