#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import has_length
from hamcrest import assert_that

import os
import json
from cStringIO import StringIO

from zope import component

from nti.badges import interfaces as badge_interfaces

from nti.app.products.badges.admin_views import bulk_import

from nti.appserver.tests.test_application import TestApp

from nti.app.products.badges.tests import NTIBadgesApplicationTestLayer

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDSHandleChanges

import nti.dataserver.tests.mock_dataserver as mock_dataserver

class TestAdminViews(ApplicationLayerTest):

	layer = NTIBadgesApplicationTestLayer

	@WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
	def test_create_persons(self):
		username = 'ichigo@bleach.com'
		with mock_dataserver.mock_db_trans(self.ds):
			self._create_user(username=username, external_value={'email':username})

		create_persons_path = '/dataserver2/BadgeAdmin/@@create_persons'
		testapp = TestApp(self.app)
		testapp.post(create_persons_path,
					 json.dumps({"term":"ichigo"}),
					 extra_environ=self._make_extra_environ(),
					 status=200)
		manager = component.getUtility(badge_interfaces.IBadgeManager, "sample")
		assert_that(manager.person_exists('ichigo@bleach.com'), is_(True))

	@WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
	def test_award(self):
		username = 'ichigo@bleach.com'
		with mock_dataserver.mock_db_trans(self.ds):
			self._create_user(username=username, external_value={'email':username})

		award_badge_path = '/dataserver2/BadgeAdmin/@@award'
		testapp = TestApp(self.app)
		testapp.post(award_badge_path,
					 json.dumps({"username":"ichigo@bleach.com",
								 "badge":"badge.1"}),
					 extra_environ=self._make_extra_environ(),
					 status=204)
		manager = component.getUtility(badge_interfaces.IBadgeManager, "sample")
		assert_that(manager.assertion_exists('ichigo@bleach.com', 'badge.1'), is_(True))

	@WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
	def test_revoke(self):
		username = 'ichigo@bleach.com'
		with mock_dataserver.mock_db_trans(self.ds):
			self._create_user(username=username, external_value={'email':username})

		award_badge_path = '/dataserver2/BadgeAdmin/@@award'
		testapp = TestApp(self.app)
		testapp.post(award_badge_path,
					 json.dumps({"username":"ichigo@bleach.com",
								 "badge":"badge.1"}),
					 extra_environ=self._make_extra_environ(),
					 status=204)

		revoke_badge_path = '/dataserver2/BadgeAdmin/@@revoke'
		testapp.post(revoke_badge_path,
					 json.dumps({"username":"ichigo@bleach.com",
								 "badge":"badge.1"}),
					 extra_environ=self._make_extra_environ(),
					 status=204)
		manager = component.getUtility(badge_interfaces.IBadgeManager, "sample")
		assert_that(manager.assertion_exists('ichigo@bleach.com', 'badge.1'), is_(False))

	@WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
	def test_bulk_import(self):
		with mock_dataserver.mock_db_trans(self.ds):
			for username in ('ichigo', 'rukia'):
				self._create_user(username=username, external_value={'email':username+'@bleach.com'})

		award_badge_path = '/dataserver2/BadgeAdmin/@@award'
		testapp = TestApp(self.app)
		testapp.post(award_badge_path,
					 json.dumps({"username":"rukia",
								 "badge":"badge.2"}),
					 extra_environ=self._make_extra_environ(),
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
		testapp = TestApp(self.app)
		testapp.post(sync_db_path,
					 json.dumps({"directory":path,
								 "dbname":"sample",
								 "verify":True}),
					 extra_environ=self._make_extra_environ(),
					 status=200)

