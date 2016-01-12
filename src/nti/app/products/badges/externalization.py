#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from collections import Mapping

from zope import component
from zope import interface

from pyramid.threadlocal import get_current_request

from nti.app.products.badges import is_locked

from nti.app.products.badges.utils import get_openbadge_url
from nti.app.products.badges.utils import get_openissuer_url
from nti.app.products.badges.utils import get_badge_image_url
from nti.app.products.badges.utils import get_assertion_json_url
from nti.app.products.badges.utils import get_assertion_image_url

from nti.badges.openbadges.interfaces import IBadgeClass
from nti.badges.openbadges.interfaces import IBadgeAssertion
from nti.badges.openbadges.interfaces import IIssuerOrganization

from nti.externalization.datastructures import InterfaceObjectIO

from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IInternalObjectExternalizer

ALL_EXTERNAL_FIELDS = getattr(StandardExternalFields, 'ALL', ())

def _clean_external(external):
	external.pop('href', None)
	external.pop('Locked', None)
	def _m(ext):
		if isinstance(ext, Mapping):
			for key in ALL_EXTERNAL_FIELDS:
				ext.pop(key, None)
			for key, value in ext.items():
				if value is None:
					ext.pop(key, None)
				else:
					_m(value)
		elif isinstance(ext, (tuple, list)):
			for value in ext:
				_m(value)
	_m(external)
	return external

@component.adapter(IBadgeAssertion)
@interface.implementer(IInternalObjectExternalizer)
class _MozillaOpenAssertionExternalizer(object):

	def __init__(self, context):
		self.context = context

	def toExternalObject(self, **kwargs):
		result = InterfaceObjectIO(self.context, IBadgeAssertion).toExternalObject(**kwargs)
		result = _clean_external(result)

		# get assertion_image
		request = get_current_request()
		if request:
			result['image'] = get_assertion_image_url(self.context, request)

		# change badge to an URL
		badge = self.context.badge
		if IBadgeClass.providedBy(badge) and request:
			result['badge'] = get_openbadge_url(badge, request)

		# change verification URL
		if is_locked(self.context):
			verify = result.get('verify')
			url = get_assertion_json_url(self.context, request)
			if url and verify:  # replace verification URL
				verify['url'] = url
		else:
			result.pop('verify', None)

		return result

@component.adapter(IBadgeClass)
@interface.implementer(IInternalObjectExternalizer)
class _MozillaOpenBadgeExternalizer(object):

	def __init__(self, context):
		self.context = context

	def toExternalObject(self, **kwargs):
		result = InterfaceObjectIO(self.context, IBadgeClass).toExternalObject(**kwargs)
		result = _clean_external(result)

		request = get_current_request()
		if request:
			result['image'] = get_badge_image_url(self.context, request)

		# change issuer url
		request = get_current_request()
		issuer = self.context.issuer
		if IIssuerOrganization.providedBy(issuer) and request:
			result['issuer'] = get_openissuer_url(issuer, request)

		result.pop('Type', None)
		return result

@component.adapter(IIssuerOrganization)
@interface.implementer(IInternalObjectExternalizer)
class _MozillaOpenIssuerExternalizer(object):

	def __init__(self, context):
		self.context = context

	def toExternalObject(self, **kwargs):
		result = InterfaceObjectIO(self.context, IIssuerOrganization).toExternalObject(**kwargs)
		result = _clean_external(result)
		return result
