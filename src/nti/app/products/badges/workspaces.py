#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Implementation of an Atom/OData workspace and collection
for badges.

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface
from zope import component
from zope.container import contained

from nti.appserver import interfaces as app_interfaces

from nti.utils.property import Lazy
from nti.utils.property import alias

from . import interfaces
from . import get_badge_manager

@interface.implementer(interfaces.IBadgesWorkspace)
class _BadgesWorkspace(contained.Contained):

	__name__ = 'Badges'
	name = alias('__name__', __name__)

	def __init__(self, user_service, manager):
		self.manager = manager
		self.context = user_service
		self.user = user_service.user

	@Lazy
	def collections(self):
		return (AllBadgesCollection(self),)

	def __getitem__(self, key):
		"Make us traversable to collections."
		for i in self.collections:
			if i.__name__ == key:
				return i
		raise KeyError(key)

	def __len__(self):
		return len(self.collections)

@interface.implementer(interfaces.IBadgesWorkspace)
@component.adapter(app_interfaces.IUserService)
def BadgesWorkspace(user_service):
	"""
	The badges for a user reside at the path ``/users/$ME/Badges``.
	"""
	manager = get_badge_manager()
	if manager:
		workspace = _BadgesWorkspace(user_service, manager)
		workspace.__parent__ = workspace.user
		return workspace

@interface.implementer(app_interfaces.IContainerCollection)
class AllBadgesCollection(contained.Contained):

	#: Our name, part of our URL.
	__name__ = 'AllBadges'
	name = alias('__name__', __name__)

	accepts = ()

	def __init__(self, parent):
		self.__parent__ = parent

	def __getitem__(self, key):
		if key == self.container.__name__:
			return self.container
		raise KeyError(key)

	def __len__(self):
		return 1

