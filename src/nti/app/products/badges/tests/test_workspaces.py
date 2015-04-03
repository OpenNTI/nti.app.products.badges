#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_key
from hamcrest import contains
from hamcrest import has_item
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

from nti.appserver.workspaces.interfaces import ICollection
from nti.appserver.workspaces.interfaces import IUserService

from nti.app.products.badges import add_assertion
from nti.app.products.badges import interfaces as app_badge_interfaces

from nti.badges.openbadges.utils.badgebakery import get_baked_data

from nti.traversal import traversal

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
														verifiably_provides(ICollection) ))

			assert_that(workspace.collections, has_items(has_property('name', 'AllBadges'),
														 has_property('name', 'EarnedBadges'),
														 has_property('name', 'EarnableBadges') ))

			assert_that( [traversal.resource_path(c) for c in workspace.collections],
						 has_items(badges_path + '/AllBadges',
								   badges_path + '/EarnedBadges',
								   badges_path + '/EarnableBadges'))

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
	@fudge.patch('nti.app.products.badges.views.get_badge_image_content',
				 'nti.app.products.badges.decorators.is_locked',
				 'nti.app.products.badges.externalization.is_locked',
				 'nti.app.products.badges.views.is_locked')
	def test_assertions(self, mock_ic, mock_ie1, mock_ie2, mock_ie3):		
		mock_ie1.is_callable().with_args().returns(True)
		mock_ie2.is_callable().with_args().returns(True)
		mock_ie3.is_callable().with_args().returns(True)

		badge_name = "badge.2"
		username = 'person.2@nti.com'
		with mock_dataserver.mock_db_trans(self.ds):
			self._create_user(username=username, external_value={'email':username})

		with mock_dataserver.mock_db_trans(self.ds):
			add_assertion(username, badge_name)

		earned_badges_path = '/dataserver2/users/person.2%40nti.com/Badges/EarnedBadges'
		testapp = TestApp(self.app)
		res = testapp.get(earned_badges_path,
						  extra_environ=self._make_extra_environ(user=username),
						  status=200)
		
		assertion_path = None
		assert_that(res.json_body, has_entry(u'Items', has_length(greater_than_or_equal_to(1))))
		item = res.json_body['Items'][0]
		assert_that(item, has_key('Links'))
		for link in item['Links']:
			if link.get('rel') == 'assertion':
				assertion_path = link['href']
			
		assert_that(assertion_path, is_not(none()))
		res = testapp.get(assertion_path,
						  extra_environ=self._make_extra_environ(user=username),
						  status=200)

		assert_that(res.json_body, has_entry('uid', is_not(none())))
		assert_that(res.json_body, has_entry(u'MimeType', u'application/vnd.nextthought.openbadges.assertion'))
		assert_that(res.json_body, has_entry(u'Links', has_length(2)))
		assert_that(res.json_body, has_entry(u'image', is_not(none())))
		assert_that(res.json_body, has_entry(u'recipient',
											 has_entry(u'MimeType', u'application/vnd.nextthought.openbadges.identityobject')))
		
		uid = res.json_body['uid'] # save uid
		
		icon  = os.path.join(os.path.dirname(__file__), 'icon.png')
		with open(icon, "rb") as fp:
			icon = fp.read()
		mock_ic.is_callable().with_args().returns(icon)

		image_assertion_path = assertion_path + "/image.png"
		res = testapp.get(image_assertion_path,
						  extra_environ=self._make_extra_environ(user=username),
						  status=200)
		data = get_baked_data(BytesIO(res.body))
		assert_that(data, has_entry('image', contains_string('http://localhost/dataserver2/OpenAssertions/')))
		
		assertion_assertion_path = assertion_path + "/assertion.json"
		res = testapp.get(assertion_assertion_path,
						  extra_environ=self._make_extra_environ(user=username),
						  status=200)
		
		assert_that(res.json_body, has_entry('uid', is_(uid)))
		assert_that(res.json_body, has_entry('issuedOn', is_not(none())))
		assert_that(res.json_body, has_entry('image', contains_string('http://localhost/dataserver2/OpenAssertions/')))
		assert_that(res.json_body, has_entry('badge', is_('http://localhost/dataserver2/OpenBadges/badge.2/badge.json')))
		assert_that(res.json_body, has_entry('verify', has_entry('url', contains_string(uid))))
		assert_that(res.json_body, has_entry('recipient', has_entry('type', is_('email'))))
		assert_that(res.json_body, has_entry('recipient', has_entry('hashed', is_(True))))
		assert_that(res.json_body, has_entry('recipient', has_entry('salt', is_not(none()))))
		assert_that(res.json_body, has_entry('recipient', has_entry('identity', is_not(none()))))
		
		badge_json_url = 'http://localhost/dataserver2/OpenBadges/badge.2/badge.json'
		res = testapp.get(badge_json_url,
						  extra_environ=self._make_extra_environ(user=username),
						  status=200)
		assert_that(res.json_body, has_entry('image', is_('http://localhost/hosted_badge_images/badge_2.png')))
		assert_that(res.json_body, has_entry('issuer', contains_string('http://localhost/dataserver2/OpenIssuers/issuer')))

		issuer_json_url = res.json_body['issuer']
		res = testapp.get(issuer_json_url,
						  extra_environ=self._make_extra_environ(user=username),
						  status=200)
		assert_that(res.json_body, has_entry('url', is_('http://nti.com')))
