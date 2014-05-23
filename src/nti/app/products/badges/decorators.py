#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from pyramid.threadlocal import get_current_request

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

