#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope.lifecycleevent.interfaces import IObjectRemovedEvent

from nti.badges import interfaces as badge_interfaces
from nti.badges.tahrir import interfaces as tahrir_interfaces

from nti.dataserver import interfaces as nti_interfaces

from nti.processlifetime import IAfterDatabaseOpenedEvent

import sqlalchemy.exc

@component.adapter(nti_interfaces.IUser, IObjectRemovedEvent)
def _user_deleted(user, event):
	manager = component.getUtility(badge_interfaces.IBadgeManager)
	if manager.person_exists(user):
		manager.delete_person(user)

@component.adapter(IAfterDatabaseOpenedEvent)
def _after_database_opened_listener(event):
	logger.info("Adding registered tahrir issuers")

	import transaction
	with transaction.manager:
		# TODO: Should probably defer this until needed
		# FIXME: It's wrong to be trying to control our own transaction here,
		# that will fail at startup under certain scenarios.
		# FIXME: Note that this event is fired for *every* configured
		# database shard. We have some hacky defense against that below.
		# It's also fired for every shard in every test case...not ideal
		issuers = {x[1] for x in component.getUtilitiesFor(tahrir_interfaces.IIssuer)}
		manager = component.getUtility(badge_interfaces.IBadgeManager)
		if getattr(manager, '_v_installed', False):
			return

		setattr(manager, str('_v_installed'), True)
		for issuer in issuers:
			if not manager.issuer_exists(issuer):
				# FIXME: Under some circumstances, we can get an
				# IntegrityError: ConstraintViolation, even though
				# this code path only checks name and origin.
				# So clearly there's some sort of race condition here.
				# Is our transaction not actually isolated? Or at the wrong level?
				try:
					manager.add_issuer(issuer)
				except sqlalchemy.exc.IntegrityError:
					logger.warn("Integrity error", exc_info=True)
				else:
					logger.debug("Issuer (%s,%s) added", issuer.name, issuer.origin)


from nti.badges.tahrir.interfaces import IAssertion
from nti.badges.openbadges.interfaces import IBadgeClass

from zope.lifecycleevent import IObjectAddedEvent

from .interfaces import SC_BADGE_EARNED

from nti.dataserver.activitystream_change import Change
from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import ACE_DENY_ALL
from nti.dataserver.authorization_acl import acl_from_aces
from nti.dataserver.authorization_acl import ace_allowing
from nti.dataserver.authorization import ACT_READ

from nti.appserver.interfaces import IUserActivityStorage

from nti.app.notabledata.interfaces import IUserNotableDataStorage

class AssertionChange(Change):
	"""
	Gives some class-level defaults that are useful
	for assertions/badges.
	"""

	# When we write this out, turn the assertion into the actual
	# badge
	def externalObjectTransformationHook(self, assertion):
		return IBadgeClass(assertion.badge)


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

@component.adapter(IAssertion, IObjectAddedEvent)
def _make_assertions_notable_to_target(assertion, event):
	"""
	When a badge assertion is recorded, the event is notable
	for the target user.
	"""
	change = AssertionChange(SC_BADGE_EARNED, assertion)

	user = IUser(assertion.person)
	# Set a creator...this may not be the best we can do in some cases
	change.creator = user

	storage = IUserNotableDataStorage(user)
	storage.store_object( change, safe=True, take_ownership=True )

	# At this point we can now put it in the default container in the
	# intid-based activity stream for the user...pending ACL work. To
	# be able to do that smoothly, we define a subclass of Change so
	# we can easily toggle the values.
	act_storage = IUserActivityStorage( user, None )
	if act_storage is not None:
		act_storage.addContainedObjectToContainer( change, '')
