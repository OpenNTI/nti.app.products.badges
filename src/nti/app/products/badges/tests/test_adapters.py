#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import assert_that
from hamcrest import has_property

from nti.dataserver.users import User

from nti.badges import interfaces

import nti.dataserver.tests.mock_dataserver as mock_dataserver
from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.badges.tests import NTIBadgesTestCase

class TestAdapters(NTIBadgesTestCase):

	def _create_user(self, username='shadow', password='temp001',
					 email='nt@nti.com'):
		ds = mock_dataserver.current_mock_ds
		usr = User.create_user(ds, username=username, password=password,
                               external_value={'email': email})
		return usr

	@WithMockDSTrans
	def test_user_to_io(self):
		user = self._create_user()
		io = interfaces.IIdentityObject(user)
		assert_that(io, has_property('identity', 'nt@nti.com'))
