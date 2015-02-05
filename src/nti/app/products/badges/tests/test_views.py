#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import none
from hamcrest import is_not
from hamcrest import has_key
from hamcrest import has_entry
from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import contains_string
does_not = is_not

import os
import fudge
import urllib
from io import BytesIO

from zope import component

from nti.badges.interfaces import IBadgeManager
from nti.badges.openbadges.utils.badgebakery import get_baked_data

from nti.dataserver.users import User
from nti.dataserver.users.utils import force_email_verification

from nti.appserver.tests.test_application import TestApp

from nti.app.products.badges.tests import NTISampleBadgesApplicationTestLayer

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDSHandleChanges

import nti.dataserver.tests.mock_dataserver as mock_dataserver

class TestViews(ApplicationLayerTest):

	layer = NTISampleBadgesApplicationTestLayer

	@WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
	@fudge.patch('nti.app.products.badges.views.get_badge_image_content')
	def test_open_badges(self, mock_ic):
		username = 'ichigo@bleach.com'
		with mock_dataserver.mock_db_trans(self.ds):
			self._create_user(username=username,
							  external_value={u'email':u'ichigo@bleach.com',
											  u'realname':u'ichigo kurosaki',
											  u'alias':u'zangetsu'})

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

		award_badge_path = '/dataserver2/BadgeAdmin/@@award'
		self.testapp.post_json(award_badge_path,
							   {"username":username,
								"badge":"badge.1"},
							   status=204)
		manager = component.getUtility(IBadgeManager)
		assertion = manager.get_assertion('ichigo@bleach.com', 'badge.1')
		assert_that(assertion, is_not(none()))
		
		open_assertion_path = '/dataserver2/OpenAssertions/%s' % urllib.quote(assertion.id)
		testapp = TestApp(self.app)
		res = testapp.get(open_assertion_path,
						  extra_environ=self._make_extra_environ(user=username),
						  status=200)
		
		assertion_json_path = open_assertion_path + "/assertion.json"
		res = testapp.get(assertion_json_path,
						  extra_environ=self._make_extra_environ(user=username),
						  status=200)
		
		assert_that(res.json_body, has_entry('badge', 
											 has_entries('criteria', 'http://nti.com/criteria/1.html',
														 'description', u'Badge 1',
														 'issuer', u'http://nti.com',
														 'name', u'badge.1')))
		
		assert_that(res.json_body, has_entries(
										'image', 'http://localhost/dataserver2/OpenAssertions/YmFkZ2UuMSAtPiA2/image.png',
										'issuedOn', is_not(none()),
										'uid', 'YmFkZ2UuMSAtPiA2'))
		
		assert_that(res.json_body, has_entry('recipient', 
											 has_entries('hashed', True,
														 'identity', is_not(none()),
														 'salt', is_not(none()),
														 'type', u'email')))
		
		assert_that(res.json_body, has_entry('verify', 
											 has_entries('type', 'hosted',
														 'url', u'http://nti.com')))
		
		assert_that(res.json_body, does_not(has_key('evidence')))
		assert_that(res.json_body, does_not(has_key('expires')))
		
		export_json_path = open_assertion_path + "/export"
		testapp.post(export_json_path,
					 extra_environ=self._make_extra_environ(user=username),
					 status=422)
		
		with mock_dataserver.mock_db_trans(self.ds):
			user = User.get_user(username)
			force_email_verification(user)
		
		icon  = os.path.join(os.path.dirname(__file__), 'icon.png')
		with open(icon, "rb") as fp:
			icon = fp.read()
		mock_ic.is_callable().with_args().returns(icon)
		res = testapp.post(export_json_path,
						   extra_environ=self._make_extra_environ(user=username),
						   status=200)
		data = get_baked_data(BytesIO(res.body))
		assert_that(data, contains_string('http://localhost/dataserver2/OpenAssertions/'))
