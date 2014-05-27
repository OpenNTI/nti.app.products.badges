#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import contains
from hamcrest import has_item
from hamcrest import has_items
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property
from hamcrest import greater_than_or_equal_to

from nti.appserver.interfaces import IUserService
from nti.appserver.interfaces import ICollection

from nti.app.products.badges import interfaces as app_badge_interfaces

from nti.dataserver import traversal

from nti.appserver.tests.test_application import TestApp

from nti.app.products.badges.tests import NTIBadgesApplicationTestLayer

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS
from nti.app.testing.decorators import WithSharedApplicationMockDSHandleChanges

import nti.dataserver.tests.mock_dataserver as mock_dataserver

from nti.testing.matchers import verifiably_provides

class TestWorkspaces(ApplicationLayerTest):

	layer = NTIBadgesApplicationTestLayer

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

			assert_that( workspace.collections, contains( verifiably_provides( ICollection ),
														  verifiably_provides( ICollection ),
														  verifiably_provides( ICollection )))

			assert_that(workspace.collections, has_items(has_property('name', 'AllBadges'),
														 has_property('name', 'EarnedBadges'),
														 has_property('name', 'EarnableBadges')))

			assert_that( [traversal.resource_path(c) for c in workspace.collections],
						 has_items(badges_path + '/AllBadges',
								   badges_path + '/EarnedBadges' ,
								   badges_path + '/EarnableBadges'))
			
	@WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
	def test_badge_queries(self):
		username = 'ichigo@bleach.com'
		with mock_dataserver.mock_db_trans(self.ds):
			self._create_user(username=username)

		all_badges_path = '/dataserver2/users/ichigo%40bleach.com/Badges/AllBadges'
		testapp = TestApp(self.app)
		res = testapp.get(all_badges_path,
						  extra_environ=self._make_extra_environ(user=username),
						  status=200)
		assert_that(res.json_body, has_entry(u'Items', has_length(greater_than_or_equal_to(5))))
