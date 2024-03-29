#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import greater_than_or_equal_to

from nti.app.products.badges import get_badge
from nti.app.products.badges import get_user_id
from nti.app.products.badges import get_all_badges

from nti.app.products.badges.tests import NTIBadgesTestCase

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.dataserver.users.users import User


class TestBadges(NTIBadgesTestCase):

    def _create_user(self, username=u'ntiuser', password=u'temp001',
                     email=u'ntiuser@nti.com', alias=u'myalias',
                     home_page=u'http://www.foo.com',
                     about=u"my bio"):
        ds = mock_dataserver.current_mock_ds
        usr = User.create_user(ds, username=username, password=password,
                               external_value={'email': email, 'alias': alias,
                                               'home_page': home_page,
                                               'about': about})
        return usr

    @WithMockDSTrans
    def test_get_user_id(self):
        user = self._create_user()
        uid = get_user_id(user)
        assert_that(uid, is_('ntiuser'))

    @WithMockDSTrans
    def test_get_badge(self):
        badge = get_badge("not found")
        assert_that(badge, is_(none()))

    @WithMockDSTrans
    def test_get_all_badges(self):
        badges = list(get_all_badges())
        assert_that(badges, has_length(greater_than_or_equal_to(0)))
