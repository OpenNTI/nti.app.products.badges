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
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import has_entries
from hamcrest import assert_that
from hamcrest import has_property
from hamcrest import contains_string

import os
from six import StringIO

from zope import component

from nti.ntiids import ntiids

from nti.badges.interfaces import IBadgeManager

from nti.dataserver.users.interfaces import IUserProfile

from nti.app.products.badges.admin_views import bulk_import

from nti.app.products.badges.tests import NTISampleBadgesApplicationTestLayer

from nti.app.pushnotifications.tests.test_digest_email import send_notable_email

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDSHandleChanges

from nti.dataserver.tests import mock_dataserver


class TestAdminViews(ApplicationLayerTest):

    layer = NTISampleBadgesApplicationTestLayer

    @WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
    def test_award(self):
        username = 'ichigo@bleach.com'
        with mock_dataserver.mock_db_trans(self.ds):
            self._create_user(
                username=username, external_value={'email': username})

        award_badge_path = '/dataserver2/BadgeAdmin/@@award'

        self.testapp.post_json(award_badge_path,
                               {"username": "ichigo@bleach.com",
                                "badge": "badge.1"},
                               status=200)
        manager = component.getUtility(IBadgeManager)
        assert_that(manager.assertion_exists(
            'ichigo@bleach.com', 'badge.1'), is_(True))

        # This had the side-effect of creating notable data about the award
        path = '/dataserver2/users/%s/Pages(%s)/RUGDByOthersThatIMightBeInterestedIn/' % \
                (username, ntiids.ROOT)
        res = self.testapp.get(path, 
                               extra_environ=self._make_extra_environ(username))
        assert_that(res.json_body, has_entry('TotalItemCount', 1))
        assert_that(res.json_body, has_entry('Items', has_length(1)))
        item = res.json_body['Items'][0]

        assert_that(item, has_entries('ChangeType', 'BadgeEarned',
                                      'Class', 'Change',
                                      'Item', has_entry('Class', 'Badge')))

        # should be notable in email
        msgs = send_notable_email(self.testapp)
        msg = msgs[0]
        assert_that(msg, contains_string('You earned a badge'))
        assert_that(msg, 
                    contains_string('src="http://localhost/hosted_badge_images/badge_1.png"'))

        # an in our activity
        path = '/dataserver2/users/%s/Activity' % username
        res = self.testapp.get(path, 
                               extra_environ=self._make_extra_environ(username))
        assert_that(res.json_body, has_entry('TotalItemCount', 1))
        assert_that(res.json_body, has_entry('Items', has_length(1)))
        item = res.json_body['Items'][0]

        assert_that(item, has_entries('ChangeType', 'BadgeEarned',
                                      'Class', 'Change',
                                      'Item', has_entry('Class', 'Badge')))

    @WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
    def test_revoke(self):
        username = 'ichigo@bleach.com'
        with mock_dataserver.mock_db_trans(self.ds):
            self._create_user(
                username=username, external_value={'email': username})

        award_badge_path = '/dataserver2/BadgeAdmin/@@award'
        res = self.testapp.post_json(award_badge_path,
                                     {"username": "ichigo@bleach.com",
                                      "badge": "badge.1"},
                                     status=200)
        assert_that(res.json_body, has_key('href'))
        open_assertion_path = res.json_body['href']
        self.testapp.get(open_assertion_path, status=200)

        revoke_badge_path = '/dataserver2/BadgeAdmin/@@revoke'
        self.testapp.post_json(revoke_badge_path,
                               {"username": "ichigo@bleach.com",
                                "badge": "badge.1"},
                               status=204)
        manager = component.getUtility(IBadgeManager)
        assert_that(manager.assertion_exists(
            'ichigo@bleach.com', 'badge.1'), is_(False))

        self.testapp.post_json(revoke_badge_path,
                               {"username": "ichigo@bleach.com",
                                "badge": "badge.1"},
                               status=404)

        self.testapp.get(open_assertion_path, status=404)
        self.testapp.get(open_assertion_path + '/image.png', status=404)

    @WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
    def test_bulk_import(self):
        with mock_dataserver.mock_db_trans(self.ds):
            for username in ('ichigo', 'rukia'):
                self._create_user(username=username,
                                  external_value={'email': username + '@bleach.com'})

        award_badge_path = '/dataserver2/BadgeAdmin/@@award'
        self.testapp.post_json(award_badge_path,
                               {"username": "rukia",
                                "badge": "badge.2"},
                               status=200)

        with mock_dataserver.mock_db_trans(self.ds):
            source = "ichigo\tbadge.1\n"
            source += "rukia\tbadge.2\trevoke\n"
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

        sync_db_path = '/dataserver2/BadgeAdmin/sync_db'
        self.testapp.post_json(sync_db_path,
                               {"directory": path,
                                "dbname": "sample",
                                "verify": True},
                               status=200)

    @WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
    def test_update_persons(self):
        manager = component.getUtility(IBadgeManager)

        username = 'ichigo'
        with mock_dataserver.mock_db_trans(self.ds):
            user = self._create_user(username=username,
                                     external_value={'email': 'foo@nt.com'})
            # create person email not verified
            manager.add_person(user)

            # update verification
            IUserProfile(user).email_verified = True
            IUserProfile(user).email = 'ichigo@bleach.org'

        person = manager.get_person(name='ichigo')
        assert_that(person, is_not(none()))
        assert_that(person, has_property('email', 'ichigo'))

        path = '/dataserver2/BadgeAdmin/update_persons'
        res = self.testapp.post_json(path, status=200)
        assert_that(res.json_body, has_entry('Total', is_(1)))

        person = manager.get_person(name='ichigo')
        assert_that(person, is_not(none()))
        assert_that(person, has_property('email', 'ichigo@bleach.org'))

        person = manager.get_person(email='ichigo@bleach.org')
        assert_that(person, is_not(none()))
