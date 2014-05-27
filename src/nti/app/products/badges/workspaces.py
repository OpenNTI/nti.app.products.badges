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

from nti.badges.interfaces import INTIBadge
from nti.badges.interfaces import INTIPerson

from nti.dataserver.datastructures import LastModifiedCopyingUserList

from nti.utils.property import Lazy
from nti.utils.property import alias

from . import interfaces
from . import get_user_id
from . import get_user_badge_managers

@interface.implementer(interfaces.IBadgesWorkspace)
class _BadgesWorkspace(contained.Contained):

	__name__ = 'Badges'
	name = alias('__name__', __name__)

	def __init__(self, user_service):
		self.context = user_service
		self.user = user_service.user

	@Lazy
	def collections(self):
		return (AllBadgesCollection(self),
				EarnableBadgeCollection(self),
				EarnedBadgeCollection(self))

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
	workspace = _BadgesWorkspace(user_service)
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

	@Lazy
	def container(self):
		parent = self.__parent__
		container = LastModifiedCopyingUserList()
		container.__parent__ = parent
		container.__name__ = __name__
		predicate = interfaces.get_badge_predicate_for_user(parent.user)
		for manager in get_user_badge_managers(parent.user):
			badges = manager.get_all_badges()
			container.extend(INTIBadge(b) for b in badges if predicate(b))
		return container

	def __getitem__(self, key):
		if key == self.container.__name__:
			return self.container
		raise KeyError(key)

	def __len__(self):
		return 1

@interface.implementer(app_interfaces.IContainerCollection)
class EarnableBadgeCollection(contained.Contained):

	# : Our name, part of our URL.
	__name__ = 'EarnableBadges'
	name = alias('__name__', __name__)

	accepts = ()

	def __init__(self, parent):
		self.__parent__ = parent

	def _has_been_earned(self, user, badge):
		person = INTIPerson(user)
		badge = INTIBadge(badge)
		for manager in get_user_badge_managers(user):
			if manager.assertion_exists(person, badge):
				return True
		return False

	@Lazy
	def container(self):
		parent = self.__parent__
		user = parent.user
		container = LastModifiedCopyingUserList()
		container.__parent__ = parent
		container.__name__ = __name__

		for subs in component.subscribers((user,), interfaces.IPrincipalErnableBadges):
			for badge in subs.iter_badges():
				if not self._has_been_earned(user, badge):
					container.append(INTIBadge(badge))
		return container

	def __len__(self):
		return len(self.container)

@interface.implementer(app_interfaces.IContainerCollection)
class EarnedBadgeCollection(contained.Contained):

	# : Our name, part of our URL.
	__name__ = 'EarnedBadges'
	name = alias('__name__', __name__)

	accepts = ()

	def __init__(self, parent):
		self.__parent__ = parent

	@Lazy
	def container(self):
		parent = self.__parent__
		container = LastModifiedCopyingUserList()
		container.__parent__ = parent
		container.__name__ = __name__
		uid = get_user_id(parent.user)
		for manager in get_user_badge_managers(parent.user):
			badges = manager.get_person_badges(uid)
			container.extend(INTIBadge(b) for b in badges)
		return container

	def __len__(self):
		return len(self.container)
