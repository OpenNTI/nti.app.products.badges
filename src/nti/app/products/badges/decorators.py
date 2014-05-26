#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import collections

from zope import component
from zope import interface

from pyramid.threadlocal import get_current_request

from nti.badges.openbadges import interfaces as open_interfaces

from nti.externalization import interfaces as ext_interfaces
from nti.externalization.singleton import SingletonDecorator

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
				href = '%s/OpenBadges/%s' % (ds2, badge_name)
				mapping['badge'] = href
