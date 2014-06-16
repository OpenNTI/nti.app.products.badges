#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import urllib
from urlparse import urljoin
from urlparse import urlparse

from zope import component
from zope import interface

from pyramid.threadlocal import get_current_request

from nti.badges import interfaces as badge_interfaces

from nti.dataserver.links import Link
from nti.dataserver.users import User
from nti.dataserver import interfaces as nti_interfaces

from nti.externalization import interfaces as ext_interfaces
from nti.externalization.singleton import SingletonDecorator
from nti.externalization.interfaces import StandardExternalFields

LINKS = StandardExternalFields.LINKS

from . import BADGES
from . import OPEN_BADGES_VIEW
from . import HOSTED_BADGE_IMAGES
from . import OPEN_ASSERTIONS_VIEW

from . import get_assertion

@component.adapter(badge_interfaces.IBadgeClass)
@interface.implementer(ext_interfaces.IExternalObjectDecorator)
class _BadgeLinkFixer(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, context, mapping):
		request = get_current_request()
		if request is None:
			return
		# add open badge URL
		ds2 = request.path_info_peek()  # e.g. /dataserver2/AllBadges
		href = '/%s/%s/%s' % (ds2, OPEN_BADGES_VIEW, urllib.quote(context.name))
		mapping['href'] = href

		if badge_interfaces.IEarnedBadge.providedBy(context):
			username = request.authenticated_userid
			user = User.get_user(username) if username else None
			assertion = get_assertion(user, context) if user is not None else None
			if assertion is not None:
				# add assertion baked image
				uid = urllib.quote(assertion.uid)
				href = '/%s/%s/%s/image.png' % (ds2, OPEN_ASSERTIONS_VIEW, uid)
				mapping['image'] = urljoin(request.host_url, href)
				return

		# image url fixer
		image = mapping.get('image')
		if not image:
			return
		scheme = urlparse(image).scheme
		if not scheme:
			image = image if image.lower().endswith('.png') else image + '.png'
			image = "%s/%s" % (urljoin(request.host_url, HOSTED_BADGE_IMAGES), image)
			mapping['image'] = image

@component.adapter(badge_interfaces.IBadgeAssertion)
@interface.implementer(ext_interfaces.IExternalObjectDecorator)
class _BadgeAssertionDecorator(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, context, mapping):
		request = get_current_request()
		if request is None:
			return
		ds2 = request.path_info_peek()
		href = '/%s/%s/%s' % (ds2, OPEN_ASSERTIONS_VIEW, urllib.quote(context.uid))
		mapping['href'] = href
		image = "%s/image.png" % urljoin(request.host_url, href)
		mapping['image'] = image

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
