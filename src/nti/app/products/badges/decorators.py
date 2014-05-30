#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import urllib
import collections

from zope import component
from zope import interface

from pyramid.threadlocal import get_current_request

from nti.badges.openbadges import interfaces as open_interfaces

from nti.dataserver.links import Link
from nti.dataserver import interfaces as nti_interfaces

from nti.externalization import interfaces as ext_interfaces
from nti.externalization.singleton import SingletonDecorator
from nti.externalization.interfaces import StandardExternalFields

LINKS = StandardExternalFields.LINKS

from . import BADGES

@interface.implementer(ext_interfaces.IExternalObjectDecorator)
class _BadgeHRefAdder(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, context, mapping):
		request = get_current_request()
		if request is not None:
			ds2 = '/'.join(request.path.split('/')[:2])
			href = '%s/OpenBadges/%s' % (ds2, context.name)
			mapping['href'] = href

@component.adapter(open_interfaces.IBadgeAssertion)
@interface.implementer(ext_interfaces.IExternalObjectDecorator)
class _BadgeAssertionDecorator(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, context, mapping):
		badge = mapping.get('badge')
		if isinstance(badge, collections.Mapping):  # We have badge class
			badge_name = badge.get('name')
			request = get_current_request()
			if badge_name and request is not None:
				ds2 = '/'.join(request.path.split('/')[:2])
				href = '%s/OpenBadges/%s' % (ds2, urllib.quote(badge_name))
				mapping['badge'] = href

@component.adapter(nti_interfaces.IUser)
@interface.implementer(ext_interfaces.IExternalMappingDecorator)
class _UserBadgesLinkDecorator(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalMapping(self, context, result):
		req = get_current_request()
		if  req is None or req.authenticated_userid is None or \
			req.authenticated_userid == context.username:
			return

		_links = result.setdefault(LINKS, [])
		_links.append(Link(context, elements=(BADGES,), rel=BADGES))
