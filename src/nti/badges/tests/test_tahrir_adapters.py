#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import assert_that
from hamcrest import has_property

from nti.dataserver.users import User

from nti.badges import tahrir_interfaces
from nti.badges import interfaces as badges_interfaces

import nti.dataserver.tests.mock_dataserver as mock_dataserver
from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.badges.tests import NTIBadgesTestCase

class TestTahrirAdapters(NTIBadgesTestCase):

	def _create_user(self, username='nt@nti.com', password='temp001',
					 email='nt@nti.com', alias='myalias',
					 home_page='http://www.foo.com',
					 about="my bio"):
		ds = mock_dataserver.current_mock_ds
		usr = User.create_user(ds, username=username, password=password,
                               external_value={'email': email, 'alias':alias,
											   'home_page':home_page,
											   'about':about})
		return usr

	@WithMockDSTrans
	def test_user_2_person_2_io(self):
		user = self._create_user()
		person = tahrir_interfaces.IPerson(user)
		assert_that(person, has_property('email', 'nt@nti.com'))
		assert_that(person, has_property('nickname', 'myalias'))
		assert_that(person, has_property('bio', 'my bio'))
		assert_that(person, has_property('website', 'http://www.foo.com'))

		io = badges_interfaces.IIdentityObject(person)
		assert_that(io, has_property('identity', 'nt@nti.com'))
