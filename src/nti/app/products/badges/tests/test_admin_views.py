#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_entry
from hamcrest import has_entries

import os
from cStringIO import StringIO

from zope import component

from nti.ntiids import ntiids

from nti.badges import interfaces as badge_interfaces

from nti.app.products.badges.admin_views import bulk_import

from nti.app.products.badges.tests import NTISampleBadgesApplicationTestLayer

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDSHandleChanges

import nti.dataserver.tests.mock_dataserver as mock_dataserver

class TestAdminViews(ApplicationLayerTest):

	layer = NTISampleBadgesApplicationTestLayer

	@WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
	def test_create_persons(self):
		username = 'ichigo@bleach.com'
		with mock_dataserver.mock_db_trans(self.ds):
			self._create_user(username=username, external_value={'email':username})

		create_persons_path = '/dataserver2/BadgeAdmin/@@create_persons'
		self.testapp.post_json(create_persons_path,
						  {"term":"ichigo"},
						  status=200)
		manager = component.getUtility(badge_interfaces.IBadgeManager)
		assert_that(manager.person_exists('ichigo@bleach.com'), is_(True))

	@WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
	def test_award(self):
		username = 'ichigo@bleach.com'
		with mock_dataserver.mock_db_trans(self.ds):
			self._create_user(username=username, external_value={'email':username})

		award_badge_path = '/dataserver2/BadgeAdmin/@@award'

		self.testapp.post_json(award_badge_path,
							   {"username":"ichigo@bleach.com",
								"badge":"badge.1"},
							   status=204)
		manager = component.getUtility(badge_interfaces.IBadgeManager)
		assert_that(manager.assertion_exists('ichigo@bleach.com', 'badge.1'), is_(True))

		# This had the side-effect of creating notable data about the award

		path = '/dataserver2/users/%s/Pages(%s)/RUGDByOthersThatIMightBeInterestedIn/' % ( username, ntiids.ROOT )
		res = self.testapp.get(path, extra_environ=self._make_extra_environ(username))
		assert_that( res.json_body, has_entry( 'TotalItemCount', 1))
		assert_that( res.json_body, has_entry( 'Items', has_length(1) ))
		item = res.json_body['Items'][0]

		assert_that( item, has_entries( 'ChangeType', 'BadgeEarned',
										'Class', 'Change',
										'Item', has_entry('Class', 'Badge')))


	@WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
	def test_revoke(self):
		username = 'ichigo@bleach.com'
		with mock_dataserver.mock_db_trans(self.ds):
			self._create_user(username=username, external_value={'email':username})

		award_badge_path = '/dataserver2/BadgeAdmin/@@award'
		self.testapp.post_json(award_badge_path,
							   {"username":"ichigo@bleach.com",
								"badge":"badge.1"},
							   status=204)

		revoke_badge_path = '/dataserver2/BadgeAdmin/@@revoke'
		self.testapp.post_json(revoke_badge_path,
							   {"username":"ichigo@bleach.com",
								"badge":"badge.1"},
							   status=204)
		manager = component.getUtility(badge_interfaces.IBadgeManager)
		assert_that(manager.assertion_exists('ichigo@bleach.com', 'badge.1'), is_(False))

	@WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
	def test_bulk_import(self):
		with mock_dataserver.mock_db_trans(self.ds):
			for username in ('ichigo', 'rukia'):
				self._create_user(username=username, external_value={'email':username+'@bleach.com'})

		award_badge_path = '/dataserver2/BadgeAdmin/@@award'
		self.testapp.post_json(award_badge_path,
							   {"username":"rukia",
								"badge":"badge.2"},
							   status=204)

		with mock_dataserver.mock_db_trans(self.ds):
			source = "ichigo\tbadge.1\n"
			source += "rukia@bleach.com\tbadge.2\trevoke\n"
			source += "aizen@bleach.com\tbadge.1\taward\n"
			source += "ichigo@bleach.com\tnotfound-badge\taward\n"
			source += "ichigo@bleach.com\tbadge.1\tinvalid\n"

			errors = []
			source = StringIO(source)
			awards, revokations = bulk_import(source, errors)
			assert_that(awards, is_(1))
			assert_that(revokations, is_(1))
			assert_that(errors, has_length(3))

	@WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
	def test_sync_db(self):
		path = os.getenv('DATASERVER_DATA_DIR') or '/tmp'

		sync_db_path = '/dataserver2/BadgeAdmin/@@sync_db'
		self.testapp.post_json(sync_db_path,
							   {"directory":path,
								"dbname":"sample",
								"verify":True},
							   status=200)
