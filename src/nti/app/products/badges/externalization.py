#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from collections import Mapping

from zope import interface
from zope import component

from pyramid.threadlocal import get_current_request

from nti.badges.openbadges.interfaces import IBadgeClass
from nti.badges.openbadges.interfaces import IBadgeAssertion

from nti.externalization.datastructures import InterfaceObjectIO

from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IInternalObjectExternalizer

ALL = getattr(StandardExternalFields, 'ALL', ())

from .utils import get_openbadge_url
from .utils import get_assertion_json_url
from .utils import get_assertion_image_url

from . import is_locked

def _clean_external(external):
	external.pop('href', None)
	external.pop('Locked', None)
	def _m(ext):
		if isinstance(ext, Mapping):
			for key in ALL:
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
		
		## get assertion_image
		request = get_current_request()
		if request:
			result['image'] = get_assertion_image_url(self.context, request)
		
		## change badge to an URL
		badge = self.context.badge
		if IBadgeClass.providedBy(badge):
			result['badge'] = get_openbadge_url(badge, request)
		
		## change verification URL
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
		result.pop('Type', None)
		return result
