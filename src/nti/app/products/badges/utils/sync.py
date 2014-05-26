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
	
def sync_db(path, dbid=None, verify=False):
	if dbid is not None:
		manager = component.getUtility(badge_interfaces.IBadgeManager, name=dbid)
		managers = (manager,)
	else:
		managers = list(component.getUtilitiesFor(badge_interfaces.IBadgeManager))
	
	if not managers:
		return  # No badge manager was foun

	results = scanner.flat_scan(path, verify)  # pairs mozilla badge/issuer
	for manager in manager:
		for badge, issuer in results:
			if issuer is None:
				logger.debug("Badge %s cannot be processed; issuer not found",
							 badge.name)
				continue
			manager.add_issuer(issuer)
			manager.add_badge(badge, issuer)
