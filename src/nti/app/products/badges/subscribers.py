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

from nti.badges.tahrir import interfaces as tahrir_interfaces

from nti.dataserver import interfaces as nti_interfaces

from nti.processlifetime import IAfterDatabaseOpenedEvent

from . import get_user_badge_managers

import sqlalchemy.exc

@component.adapter(nti_interfaces.IUser, IObjectRemovedEvent)
def _user_deleted(user, event):
	for manager in get_user_badge_managers(user):
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
		managers = {x[1] for x in component.getUtilitiesFor(tahrir_interfaces.ITahrirBadgeManager)}
		for manager in managers:
			if getattr(manager, '_v_installed', False):
				continue

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
