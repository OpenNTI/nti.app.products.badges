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

from zope import component
from zope import interface

from nti.app.renderers.decorators import AbstractAuthenticatedRequestAwareDecorator

from nti.badges.interfaces import IBadgeClass
from nti.badges.interfaces import IBadgeAssertion

from nti.dataserver.links import Link
from nti.dataserver.interfaces import IUser

from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IExternalMappingDecorator

LINKS = StandardExternalFields.LINKS

from . import BADGES
from . import OPEN_ASSERTIONS_VIEW

from .utils import get_badge_image_url_and_href

def is_exported(context):
	result = getattr(context, 'exported', None) or False
	return result

@component.adapter(IBadgeClass)
@interface.implementer(IExternalMappingDecorator)
class _BadgeLinkFixer(AbstractAuthenticatedRequestAwareDecorator):

	def _do_decorate_external(self, context, mapping):
		request = self.request
		image, href = get_badge_image_url_and_href(context, request, self.remoteUser)	
		mapping['href'] = href
		mapping['image'] = image

@component.adapter(IBadgeAssertion)
@interface.implementer(IExternalMappingDecorator)
class _BadgeAssertionDecorator(AbstractAuthenticatedRequestAwareDecorator):

	def _do_decorate_external(self, context, mapping):
		request = self.request
		try:
			ds2 = request.path_info_peek() # e.g. /dataserver2
		except AttributeError:
			return
		
		url_links = (('image', 'image.png'),)
		if is_exported(context):
			url_links += (('assertion', 'assertion.json'),)
		else:
			url_links += (('export', 'export'),)

		href = '/%s/%s/%s' % (ds2, OPEN_ASSERTIONS_VIEW, quote(context.uid))
		mapping['href'] = href
		
		for key, name in url_links:
			url = "%s/%s" % (urljoin(request.host_url, href), name)
			mapping[key] = url

@component.adapter(IUser)
@interface.implementer(IExternalMappingDecorator)
class _UserBadgesLinkDecorator(AbstractAuthenticatedRequestAwareDecorator):

	def _do_decorate_external(self, context, mapping):
		_links = mapping.setdefault(LINKS, [])
		_links.append(Link(context, elements=(BADGES,), rel=BADGES))
