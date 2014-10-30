#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import contains
from hamcrest import has_item
from hamcrest import ends_with
from hamcrest import has_items
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property
from hamcrest import contains_string
from hamcrest import greater_than_or_equal_to

import os
import fudge
from io import BytesIO

from nti.appserver.interfaces import IUserService
from nti.appserver.interfaces import ICollection

from nti.app.products.badges import add_assertion
from nti.app.products.badges import interfaces as app_badge_interfaces

from nti.badges.openbadges.utils.badgebakery import get_baked_data

from nti.dataserver import traversal

from nti.appserver.tests.test_application import TestApp

from nti.app.products.badges.tests import sample_size
from nti.app.products.badges.tests import NTISampleBadgesApplicationTestLayer

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS
from nti.app.testing.decorators import WithSharedApplicationMockDSHandleChanges

import nti.dataserver.tests.mock_dataserver as mock_dataserver

from nti.testing.matchers import verifiably_provides

class TestWorkspaces(ApplicationLayerTest):

	layer = NTISampleBadgesApplicationTestLayer

	@WithSharedApplicationMockDS
	def test_workspace_links_in_service(self):
		with mock_dataserver.mock_db_trans(self.ds):
			user = self._create_user(username=self.extra_environ_default_user)
			service = IUserService(user)

			workspaces = service.workspaces

			assert_that(workspaces,
						has_item(verifiably_provides(app_badge_interfaces.IBadgesWorkspace)))

			workspace = [x for x in workspaces if app_badge_interfaces.IBadgesWorkspace.providedBy(x)][0]

			badges_path = '/dataserver2/users/sjohnson%40nextthought.COM/Badges'
			assert_that( traversal.resource_path( workspace ),
						 is_(badges_path))

			assert_that(workspace.collections, contains(verifiably_provides(ICollection),
														verifiably_provides(ICollection),
														verifiably_provides(ICollection),
														verifiably_provides(ICollection)))

			assert_that(workspace.collections, has_items(has_property('name', 'AllBadges'),
														 has_property('name', 'EarnedBadges'),
														 has_property('name', 'EarnableBadges'),
														 has_property('name', 'Assertions')))

			assert_that( [traversal.resource_path(c) for c in workspace.collections],
						 has_items(badges_path + '/AllBadges',
								   badges_path + '/EarnedBadges',
								   badges_path + '/EarnableBadges',
								   badges_path + '/Assertions'))

	@WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
	def test_all_badges(self):
		username = 'ichigo@bleach.com'
		with mock_dataserver.mock_db_trans(self.ds):
			self._create_user(username=username)

		all_badges_path = '/dataserver2/users/ichigo%40bleach.com/Badges/AllBadges'
		testapp = TestApp(self.app)
		res = testapp.get(all_badges_path,
						  extra_environ=self._make_extra_environ(user=username),
						  status=200)
		assert_that(res.json_body, has_entry(u'Items', has_length(greater_than_or_equal_to(sample_size))))

	@WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
	def test_earned_badges(self):
		badge_name = "badge.1"
		username = 'person.1@nti.com'
		with mock_dataserver.mock_db_trans(self.ds):
			self._create_user(username=username, external_value={'email':username})

		earned_badges_path = '/dataserver2/users/person.1%40nti.com/Badges/EarnedBadges'
		testapp = TestApp(self.app)
		res = testapp.get(earned_badges_path,
						  extra_environ=self._make_extra_environ(user=username),
						  status=200)
		assert_that(res.json_body, has_entry(u'Items', has_length(greater_than_or_equal_to(0))))

		with mock_dataserver.mock_db_trans(self.ds):
			add_assertion(username, badge_name)

		res = testapp.get(earned_badges_path,
						  extra_environ=self._make_extra_environ(user=username),
						  status=200)
		assert_that(res.json_body, has_entry(u'Items', has_length(greater_than_or_equal_to(1))))

	@WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
	def test_earnable_badges(self):
		username = 'person.1@nti.com'
		with mock_dataserver.mock_db_trans(self.ds):
			self._create_user(username=username, external_value={'email':username})

		earned_badges_path = '/dataserver2/users/person.1%40nti.com/Badges/EarnableBadges'
		testapp = TestApp(self.app)
		res = testapp.get(earned_badges_path,
						  extra_environ=self._make_extra_environ(user=username),
						  status=200)
		assert_that(res.json_body, has_entry(u'Items', has_length(greater_than_or_equal_to(0))))

	@WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
	@fudge.patch('nti.app.products.badges.views.get_badge_image_content')
	def test_assertions(self, mock_ic):
		badge_name = "badge.2"
		username = 'person.2@nti.com'
		with mock_dataserver.mock_db_trans(self.ds):
			self._create_user(username=username, external_value={'email':username})

		with mock_dataserver.mock_db_trans(self.ds):
			add_assertion(username, badge_name)

		earned_badges_path = '/dataserver2/users/person.2%40nti.com/Badges/Assertions'
		testapp = TestApp(self.app)
		res = testapp.get(earned_badges_path,
						  extra_environ=self._make_extra_environ(user=username),
						  status=200)
		
		assert_that(res.json_body, has_entry(u'Items', has_length(greater_than_or_equal_to(1))))
		item = res.json_body['Items'][0]
		assert_that(item, has_entry('uid', is_not(none())))
		assert_that(item, has_entry('href', is_not(none())))
		
		assertion_path = item['href']
		res = testapp.get(assertion_path,
						  extra_environ=self._make_extra_environ(user=username),
						  status=200)

		uid = item['uid']
		assert_that(res.json_body, has_entry('uid', uid))
		assert_that(res.json_body, has_entry(u'MimeType', u'application/vnd.nextthought.openbadges.assertion'))
		assert_that(res.json_body, has_entry(u'image', ends_with(uid + '/image.png')))
		assert_that(res.json_body, has_entry(u'assertion', ends_with(uid + '/assertion.json')))
		assert_that(res.json_body, has_entry(u'recipient',
											 has_entry(u'MimeType', u'application/vnd.nextthought.openbadges.identityobject')))
		
		icon  = os.path.join(os.path.dirname(__file__), 'icon.png')
		with open(icon, "rb") as fp:
			icon = fp.read()
		mock_ic.is_callable().with_args().returns(icon)

		image_assertion_path = assertion_path + "/image.png"
		res = testapp.get(image_assertion_path,
						  extra_environ=self._make_extra_environ(user=username),
						  status=200)
		data = get_baked_data(BytesIO(res.body))
		assert_that(data, contains_string('http://localhost/dataserver2/OpenAssertions/'))
