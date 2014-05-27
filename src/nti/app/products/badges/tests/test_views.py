#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import has_entry
from hamcrest import assert_that

import urllib

from nti.appserver.tests.test_application import TestApp

from nti.app.products.badges.tests import NTIBadgesApplicationTestLayer

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDSHandleChanges

import nti.dataserver.tests.mock_dataserver as mock_dataserver

class TestViews(ApplicationLayerTest):

	layer = NTIBadgesApplicationTestLayer
			
	@WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
	def test_open_badges(self):
		username = 'ichigo@bleach.com'
		with mock_dataserver.mock_db_trans(self.ds):
			self._create_user(username=username)

		badge_name = urllib.quote("badge.1")
		open_badges_path = '/dataserver2/OpenBadges/%s' % badge_name
		testapp = TestApp(self.app)
		res = testapp.get(open_badges_path,
						  extra_environ=self._make_extra_environ(user=username),
						  status=200)
		assert_that(res.json_body, has_entry(u'name', 'badge.1'))
		assert_that(res.json_body, has_entry(u'href', '/dataserver2/OpenBadges/badge.1'))
		assert_that(res.json_body, has_entry(u'image', 'http://nti.com/files/badge_1.png'))
		assert_that(res.json_body, has_entry(u'criteria', 'http://nti.com/criteria/1.html'))

