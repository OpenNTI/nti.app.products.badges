#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from urllib import quote
from urlparse import urljoin
from urlparse import urlparse

from zope import component
from zope import interface

from nti.app.renderers.decorators import AbstractAuthenticatedRequestAwareDecorator

from nti.badges.interfaces import IBadgeClass
from nti.badges.interfaces import IBadgeAssertion
from nti.badges import interfaces as badge_interfaces

from nti.dataserver.links import Link
from nti.dataserver.interfaces import IUser

from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IExternalMappingDecorator

LINKS = StandardExternalFields.LINKS

from . import BADGES
from . import OPEN_BADGES_VIEW
from . import HOSTED_BADGE_IMAGES
from . import OPEN_ASSERTIONS_VIEW

from . import get_assertion

@component.adapter(IBadgeClass)
@interface.implementer(IExternalMappingDecorator)
class _BadgeLinkFixer(AbstractAuthenticatedRequestAwareDecorator):

	def _do_decorate_external(self, context, mapping):
		request = self.request
		
		# add open badge URL
		ds2 = request.path_info_peek()  # e.g. /dataserver2/AllBadges
		href = '/%s/%s/%s' % (ds2, OPEN_BADGES_VIEW, quote(context.name))
		mapping['href'] = href

		if badge_interfaces.IEarnedBadge.providedBy(context):
			user = self.remoteUser
			assertion = get_assertion(user, context) if user is not None else None
			if assertion is not None:
				# add assertion baked image
				uid = quote(assertion.uid)
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

@component.adapter(IBadgeAssertion)
@interface.implementer(IExternalMappingDecorator)
class _BadgeAssertionDecorator(AbstractAuthenticatedRequestAwareDecorator):

	def _do_decorate_external(self, context, mapping):
		request = self.request
		ds2 = request.path_info_peek()
		href = '/%s/%s/%s' % (ds2, OPEN_ASSERTIONS_VIEW, quote(context.uid))
		mapping['href'] = href
		image = "%s/image.png" % urljoin(request.host_url, href)
		mapping['image'] = image

@component.adapter(IUser)
@interface.implementer(IExternalMappingDecorator)
class _UserBadgesLinkDecorator(AbstractAuthenticatedRequestAwareDecorator):

	def _do_decorate_external(self, context, mapping):
		_links = mapping.setdefault(LINKS, [])
		_links.append(Link(context, elements=(BADGES,), rel=BADGES))
