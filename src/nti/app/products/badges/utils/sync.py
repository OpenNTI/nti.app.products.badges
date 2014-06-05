#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from nti.badges.openbadges.utils import scanner
from nti.badges import interfaces as badge_interfaces

def sync_db(path, dbid=None, verify=False, **kwargs):
	badges = 0
	issuers = 0
	if dbid is not None:
		manager = component.getUtility(badge_interfaces.IBadgeManager, name=dbid)
		managers = (dbid, manager)
	else:
		managers = list(component.getUtilitiesFor(badge_interfaces.IBadgeManager))

	if not managers:
		return  # No badge manager was found

	results = scanner.flat_scan(path, verify=verify, **kwargs)  # pairs mozilla badge/issuer
	for _, manager in managers:
		for badge, issuer in results:
			if issuer is None:
				logger.debug("Badge %s cannot be processed; issuer not found",
							 badge.name)
				continue

			if not manager.issuer_exists(issuer):
				issuers += 1
				manager.add_issuer(issuer)
				logger.debug("Issuer %s,%s added", issuer.name, issuer.url)

			if not manager.badge_exists(badge):
				badges += 1
				manager.add_badge(badge, issuer)
				logger.debug('Badge %s added', badge.name)

	return (issuers, badges)
