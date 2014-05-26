#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import has_length
from hamcrest import assert_that

from nti.dataserver.users import User

from nti.app.products.badges import get_user_id
from nti.app.products.badges import get_user_badge_managers

import nti.dataserver.tests.mock_dataserver as mock_dataserver
from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.app.products.badges.tests import NTIBadgesTestCase

class TestBadges(NTIBadgesTestCase):

	def _create_user(self, username='ntiuser', password='temp001',
					 email='ntiuser@nti.com', alias='myalias',
					 home_page='http://www.foo.com',
					 about="my bio"):
		ds = mock_dataserver.current_mock_ds
		usr = User.create_user(ds, username=username, password=password,
                               external_value={'email': email, 'alias':alias,
											   'home_page':home_page,
											   'about':about})
		return usr


	@WithMockDSTrans
	def test_get_user_id(self):
		user = self._create_user()
		uid = get_user_id(user)
		assert_that(uid, is_('ntiuser'))

	@WithMockDSTrans
	def test_get_user_badge_managers(self):
		user = self._create_user()
		managers = list(get_user_badge_managers(user))
		assert_that(managers, has_length(1))
