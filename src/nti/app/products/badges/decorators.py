#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.app.renderers.decorators import AbstractAuthenticatedRequestAwareDecorator

from nti.badges.interfaces import IBadgeClass
from nti.badges.interfaces import IEarnedBadge
from nti.badges.interfaces import IBadgeAssertion
from nti.badges.openbadges.interfaces import IBadgeAssertion as IOpenAssertion

from nti.dataserver.interfaces import IUser

from nti.externalization.singleton import SingletonDecorator
from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IExternalObjectDecorator
from nti.externalization.interfaces import IExternalMappingDecorator

from nti.links.links import Link

from . import BADGES

from . import is_locked
from . import get_assertion
from . import is_email_verified

from .utils import get_badge_href
from .utils import get_assertion_href
from .utils import get_badge_image_url
from .utils import get_assertion_json_url
from .utils import get_assertion_image_url

LINKS = StandardExternalFields.LINKS

def _assertion_links(links, context, remoteUser, request):
	locked = is_locked(context)
	if locked:
		## add linkt baked image
		href = get_assertion_image_url(context, request)
		links.append(Link(href, rel='baked-image'))
		## add link to assertion json
		href = get_assertion_json_url(context, request)
		links.append(Link(href, rel='mozilla-backpack'))
	elif is_email_verified(remoteUser):
		## add link to export/lock assertion
		href = get_assertion_href(context, request)
		links.append(Link(href, elements=('lock',), rel='lock'))
	return locked
			
@component.adapter(IBadgeClass)
@interface.implementer(IExternalMappingDecorator)
class _BadgeLinkFixer(AbstractAuthenticatedRequestAwareDecorator):

	def _do_decorate_external(self, context, mapping):
		request = self.request
		mapping['href'] = get_badge_href(context, request)
		mapping['image'] = get_badge_image_url(context, request)
		if IEarnedBadge.providedBy(context):
			assertion = get_assertion(self.remoteUser, context)
			if assertion is not None:
				_links = mapping.setdefault(LINKS, [])
				href = get_assertion_href(assertion, request) 
				_links.append(Link(href, rel="assertion"))
				locked = _assertion_links(_links, assertion, self.remoteUser, request)
				mapping['Locked'] = locked
				
@component.adapter(IBadgeAssertion)
@interface.implementer(IExternalMappingDecorator)
class _BadgeAssertionDecorator(AbstractAuthenticatedRequestAwareDecorator):

	def _do_decorate_external(self, context, mapping):
		request = self.request
		_links = mapping.setdefault(LINKS, [])
		mapping['href'] = get_assertion_href(context, request)
		mapping['image'] = get_assertion_image_url(context, request)
		locked = _assertion_links(_links, context, self.remoteUser, request)
		mapping['Locked'] = locked

@component.adapter(IOpenAssertion)
@interface.implementer(IExternalObjectDecorator)
class _OpenAssertionDecorator(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, context, external):
		if not is_locked(context):
			external.pop('verify', None)

@component.adapter(IUser)
@interface.implementer(IExternalMappingDecorator)
class _UserBadgesLinkDecorator(AbstractAuthenticatedRequestAwareDecorator):

	def _do_decorate_external(self, context, mapping):
		_links = mapping.setdefault(LINKS, [])
		_links.append(Link(context, elements=(BADGES,), rel=BADGES))
