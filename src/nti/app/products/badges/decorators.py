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

from pyramid.threadlocal import get_current_request

from nti.app.renderers.decorators import AbstractAuthenticatedRequestAwareDecorator

from nti.badges.interfaces import IBadgeClass
from nti.badges.interfaces import IBadgeAssertion
from nti.badges.openbadges.interfaces import IBadgeAssertion as IOpenAssertion

from nti.dataserver.interfaces import IUser

from nti.externalization.singleton import SingletonDecorator
from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IExternalObjectDecorator
from nti.externalization.interfaces import IExternalMappingDecorator

from nti.links.links import Link

from . import BADGES
from . import OPEN_ASSERTIONS_VIEW

from . import is_locked
from . import is_email_verified

from .utils import get_badge_image_url_and_href

LINKS = StandardExternalFields.LINKS

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

		url_links = ( ('image', 'image.png'), )
		if is_locked(context):
			url_links += ( ('assertion', 'assertion.json'), )
		elif is_email_verified(self.remoteUser):
			url_links += ( ('export', 'export'), )

		href = '/%s/%s/%s' % (ds2, OPEN_ASSERTIONS_VIEW, quote(context.uid))
		mapping['href'] = href
		
		_links = mapping.setdefault(LINKS, [])
		for key, name in url_links:
			_links.append(Link(href, elements=(name,), rel=key))
			if key == 'image': # legacy
				url = "%s/%s" % (urljoin(request.host_url, href), name)
				mapping[key] = url

@component.adapter(IUser)
@interface.implementer(IExternalMappingDecorator)
class _UserBadgesLinkDecorator(AbstractAuthenticatedRequestAwareDecorator):

	def _do_decorate_external(self, context, mapping):
		_links = mapping.setdefault(LINKS, [])
		_links.append(Link(context, elements=(BADGES,), rel=BADGES))

@component.adapter(IOpenAssertion)
@interface.implementer(IExternalObjectDecorator)
class _OpenAssertionDecorator(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, original, external):
		request = get_current_request()
		if request is None:
			return
		try:
			ds2 = request.path_info_peek() # e.g. /dataserver2
		except AttributeError:
			return
		
		if is_locked(original):	
			href = '/%s/%s/%s' % (ds2, OPEN_ASSERTIONS_VIEW, quote(original.uid))
			verify = external.get('verify')
			if verify:
				verify['url'] = urljoin(request.host_url, href)
