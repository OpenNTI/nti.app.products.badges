#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Implementation of an Atom/OData workspace and collection for badges.

.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from zope.cachedescriptors.property import Lazy

from zope.container.contained import Contained

from nti.appserver.workspaces.interfaces import IUserService
from nti.appserver.workspaces.interfaces import IContainerCollection

from nti.app.products.badges import BADGES
from nti.app.products.badges import OPEN_BADGES_VIEW
from nti.app.products.badges import OPEN_ISSUERS_VIEW
from nti.app.products.badges import OPEN_ASSERTIONS_VIEW

from nti.app.products.badges import get_all_badges
from nti.app.products.badges import assertion_exists
from nti.app.products.badges import get_person_badges
from nti.app.products.badges import get_person_assertions

from nti.app.products.badges.interfaces import IBadgesWorkspace
from nti.app.products.badges.interfaces import IOpenBadgeAdapter
from nti.app.products.badges.interfaces import IPrincipalErnableBadges
from nti.app.products.badges.interfaces import get_principal_badge_filter
from nti.app.products.badges.interfaces import get_principal_earned_badge_filter
from nti.app.products.badges.interfaces import get_principal_earnable_badge_filter

from nti.badges.interfaces import IEarnedBadge
from nti.badges.interfaces import IBadgeManager
from nti.badges.interfaces import IEarnableBadge

from nti.badges.openbadges.interfaces import IBadgeClass
from nti.badges.openbadges.interfaces import IBadgeAssertion

from nti.dataserver.interfaces import IDataserverFolder

from nti.datastructures.datastructures import LastModifiedCopyingUserList

from nti.links.links import Link

from nti.property.property import alias

from nti.traversal.traversal import find_interface


def get_openbadge(context):
    adapter = component.queryUtility(IOpenBadgeAdapter)
    result = adapter.adapt(context) if adapter else None
    result = IBadgeClass(context) if result is None else result
    return result


@interface.implementer(IBadgesWorkspace)
class _BadgesWorkspace(Contained):

    __name__ = BADGES

    name = alias('__name__', __name__)

    def __init__(self, user_service):
        self.context = user_service
        self.user = user_service.user

    @Lazy
    def collections(self):
        # If there is no badge manager for this site,
        # don't even try to pretend we have collections
        if component.queryUtility(IBadgeManager) is not None:
            return (AllBadgesCollection(self),
                    EarnableBadgeCollection(self),
                    EarnedBadgeCollection(self))
        return ()

    @property
    def links(self):
        result = []
        link_names = [OPEN_BADGES_VIEW,
                      OPEN_ISSUERS_VIEW,
                      OPEN_ASSERTIONS_VIEW]
        ds_folder = find_interface(self, IDataserverFolder, strict=True)
        for name in link_names:
            link = Link(ds_folder, rel=name, elements=(name,))
            result.append(link)
        return result

    def __getitem__(self, key):
        """
        Make us traversable to collections.
        """
        for i in self.collections:
            if i.__name__ == key:
                return i
        raise KeyError(key)

    def __len__(self):
        return len(self.collections)


@interface.implementer(IBadgesWorkspace)
@component.adapter(IUserService)
def BadgesWorkspace(user_service):
    """
    The badges for a user reside at the path ``/users/$ME/Badges``.
    """
    workspace = _BadgesWorkspace(user_service)
    workspace.__parent__ = workspace.user
    return workspace


@interface.implementer(IContainerCollection)
class AllBadgesCollection(Contained):

    #: Our name, part of our URL.
    __name__ = u'AllBadges'

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
        all_badges = get_all_badges()
        predicate = get_principal_badge_filter(parent.user)
        container.extend(get_openbadge(b) for b in all_badges if predicate(b))
        return container

    def __getitem__(self, key):
        if key == self.container.__name__:
            return self.container
        raise KeyError(key)

    def __len__(self):
        return 1


@interface.implementer(IContainerCollection)
class EarnableBadgeCollection(Contained):

    #: Our name, part of our URL.
    __name__ = u'EarnableBadges'

    name = alias('__name__', __name__)

    accepts = ()

    def __init__(self, parent):
        self.__parent__ = parent

    @Lazy
    def container(self):
        parent = self.__parent__
        user = parent.user
        container = LastModifiedCopyingUserList()
        container.__parent__ = parent
        container.__name__ = __name__
        predicate = get_principal_earnable_badge_filter(parent.user)
        for subs in component.subscribers((user,), IPrincipalErnableBadges):
            for badge in subs.iter_badges():
                if not assertion_exists(user, badge) and predicate(badge):
                    badge = get_openbadge(badge)
                    interface.alsoProvides(badge, IEarnableBadge)
                    container.append(badge)
        return container

    def __len__(self):
        return len(self.container)


@interface.implementer(IContainerCollection)
class EarnedBadgeCollection(Contained):

    #: Our name, part of our URL.
    __name__ = u'EarnedBadges'

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
        predicate = get_principal_earned_badge_filter(parent.user)
        person_badges = get_person_badges(parent.user)
        for badge in person_badges:
            if predicate(badge):
                badge = get_openbadge(badge)
                interface.alsoProvides(badge, IEarnedBadge)
                container.append(badge)
        return container

    def __len__(self):
        return len(self.container)


@interface.implementer(IContainerCollection)
class AssertionCollection(Contained):

    # Our name, part of our URL.
    __name__ = u'Assertions'
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
        predicate = get_principal_earned_badge_filter(parent.user)
        assertions = get_person_assertions(parent.user)
        for assertion in assertions:
            assertion = IBadgeAssertion(assertion)
            if predicate(assertion.badge):
                container.append(assertion)
        return container

    def __len__(self):
        return len(self.container)
