#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904
import unittest

import fudge

from hamcrest import assert_that
from hamcrest import has_item
from hamcrest import has_key
from hamcrest import has_property
from hamcrest import not_
from hamcrest import has_entry
from hamcrest import not_none

from nti.dataserver.interfaces import IUser

from zope import component
from zope import interface

from zope.component.hooks import site

from nti.app.saml.tests.test_logon import IsolatedComponents

from nti.badges.interfaces import IBadgeManager

from nti.site.transient import TrivialSite

from ..decorators import _UserBadgesLinkDecorator


class TestDecorators(unittest.TestCase):

    def _user(self):
        inst = fudge.Fake('User')
        interface.alsoProvides(inst, IUser)
        return inst

    def _decorate(self, inst):
        result = {}
        decorator = _UserBadgesLinkDecorator(object(), None)
        decorator.decorateExternalMapping(inst, result)
        return result

    def _test_badges_decorator(self, badge_manager):
        with site(TrivialSite(IsolatedComponents('nti.app.products.badges.tests',
                                                 bases=(component.getSiteManager(),)))):
            sm = component.getSiteManager()

            orig_manager = sm.queryUtility(IBadgeManager)
            try:
                sm.registerUtility(badge_manager, IBadgeManager)

                return self._decorate(self._user())
            finally:
                sm.registerUtility(orig_manager, IBadgeManager)

    def test_badges_decorator_on(self):
        manager = fudge.Fake('BadgeManager')
        interface.alsoProvides(manager, IBadgeManager)

        result = self._test_badges_decorator(manager)

        assert_that(result, not_none())
        assert_that(result, has_entry('Links',
                                      has_item(has_property('rel', 'Badges'))))

    def test_badges_decorator_off(self):
        manager = None

        result = self._test_badges_decorator(manager)

        assert_that(result, not_none())
        assert_that(result, not_(has_key('Links')))
