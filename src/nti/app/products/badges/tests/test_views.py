#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_key
from hamcrest import has_item
from hamcrest import has_entry
from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import contains_string
does_not = is_not

import os
import fudge
from io import BytesIO
from six.moves.urllib_parse import quote

from zope import component

from nti.app.products.badges.tests import NTISampleBadgesApplicationTestLayer

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDSHandleChanges

from nti.appserver.tests.test_application import TestApp

from nti.badges.interfaces import IBadgeManager

from nti.badges.openbadges.interfaces import IBadgeClass as IOpenBadgeClass

from nti.badges.openbadges.utils.badgebakery import get_baked_data

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.users.users import User

from nti.dataserver.users.utils import force_email_verification


class TestViews(ApplicationLayerTest):

    layer = NTISampleBadgesApplicationTestLayer

    @WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
    def test_open_issuers(self):
        issuer_name = quote("issuer_1")
        open_issuers_path = '/dataserver2/OpenIssuers/%s/@@issuer.json' % issuer_name
        # pylint: disable=no-member
        testapp = TestApp(self.app)
        testapp.get(open_issuers_path, status=200)

    @WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
    @fudge.patch('nti.app.products.badges.views.get_badge_image_content')
    def test_open_badges(self, mock_ic):
        username = u'ichigo@bleach.com'
        with mock_dataserver.mock_db_trans(self.ds):
            self._create_user(username=username,
                              external_value={'email': u'ichigo@bleach.com',
                                              'realname': u'ichigo kurosaki',
                                              'alias': u'zangetsu'})

        badge_name = quote("badge.1")
        open_badges_path = '/dataserver2/OpenBadges/%s' % badge_name
        # pylint: disable=no-member
        testapp = TestApp(self.app)
        res = testapp.get(open_badges_path,
                          extra_environ=self._make_extra_environ(user=username),
                          status=200)
        assert_that(res.json_body,
                    has_entry('name', 'badge.1'))
        assert_that(res.json_body,
                    has_entry('href', '/dataserver2/OpenBadges/badge.1'))
        assert_that(res.json_body,
                    has_entry('image', 'http://localhost/hosted_badge_images/badge_1.png'))
        assert_that(res.json_body,
                    has_entry('criteria', 'http://nti.com/criteria/1.html'))

        award_badge_path = '/dataserver2/BadgeAdmin/@@award'
        self.testapp.post_json(award_badge_path,
                               {"username": username,
                                "badge": "badge.1"},
                               status=200)

        with mock_dataserver.mock_db_trans(self.ds):
            manager = component.getUtility(IBadgeManager)
            assertion = manager.get_assertion('ichigo@bleach.com', 'badge.1')
        
            assert_that(assertion, is_not(none()))
            open_badge = IOpenBadgeClass(assertion, None)
            assert_that(open_badge, is_not(none()))

            open_assertion_path = '/dataserver2/OpenAssertions/%s' % quote(
                assertion.id)
        testapp = TestApp(self.app)
        res = testapp.get(open_assertion_path,
                          extra_environ=self._make_extra_environ(user=username),
                          status=200)

        assertion_json_path = open_assertion_path + "/assertion.json"
        res = testapp.get(assertion_json_path,
                          extra_environ=self._make_extra_environ(user=username),
                          status=422)

        export_assertion_path = open_assertion_path + "/lock"
        testapp.post(export_assertion_path,
                     extra_environ=self._make_extra_environ(user=username),
                     status=422)

        with mock_dataserver.mock_db_trans(self.ds):
            user = User.get_user(username)
            force_email_verification(user)

        icon = os.path.join(os.path.dirname(__file__), 'icon.png')
        with open(icon, "r") as fp:
            icon = fp.read()
        mock_ic.is_callable().with_args().returns(icon)
        res = testapp.post(export_assertion_path,
                           extra_environ=self._make_extra_environ(user=username),
                           status=200)
        data = get_baked_data(BytesIO(res.body))
        assert_that(data,
                    has_entry('image',
                              contains_string('http://localhost/dataserver2/OpenAssertions/')))

        baked_image_path = open_assertion_path + "/image.png"
        res = testapp.get(baked_image_path,
                          extra_environ=self._make_extra_environ(user=username),
                          status=200)
        data = get_baked_data(BytesIO(res.body))
        assert_that(data,
                    has_entry('image',
                              contains_string('http://localhost/dataserver2/OpenAssertions/')))

        assertion_json_path = open_assertion_path + "/assertion.json"
        res = testapp.get(assertion_json_path,
                          extra_environ=self._make_extra_environ(user=username),
                          status=200)

        assert_that(res.json_body,
                    has_entry('badge', 'http://localhost/dataserver2/OpenBadges/badge.1/badge.json'))

        assert_that(res.json_body,
                    has_entries('image', 'http://localhost/dataserver2/OpenAssertions/f35d4fc8b4f1294aeac14ef865bef15c/image.png',
                                'issuedOn', is_not(none()),
                                'uid', 'f35d4fc8b4f1294aeac14ef865bef15c'))

        assert_that(res.json_body,
                    has_entry('recipient',
                              has_entries('hashed', True,
                                          'identity', is_not(none()),
                                          'salt', is_not(none()),
                                          'type', 'email')))

        assert_that(res.json_body, has_entry('verify',
                                             has_entries('type', 'hosted',
                                                         'url', contains_string('http://localhost'))))

        assert_that(res.json_body, does_not(has_key('evidence')))
        assert_that(res.json_body, does_not(has_key('expires')))

    @WithSharedApplicationMockDSHandleChanges(users=True, testapp=True)
    @fudge.patch('nti.app.products.badges.views.is_email_verified')
    @fudge.patch('nti.app.products.badges.decorators.is_earned_badge')
    def test_lock_badge(self, mock_ic, mock_ieb):
        mock_ic.is_callable().with_args().returns(True)
        mock_ieb.is_callable().with_args().returns(True)
        username = u'ichigo@bleach.com'
        with mock_dataserver.mock_db_trans(self.ds):
            self._create_user(username=username,
                              external_value={'email': u'ichigo@bleach.com',
                                              'realname': u'ichigo kurosaki',
                                              'alias': u'zangetsu'})

        badge_name = quote("badge.1")
        award_badge_path = '/dataserver2/OpenBadges/%s/@@award' % badge_name
        self.testapp.post_json(award_badge_path,
                               {"username": username},
                               status=200)

        badge_name = quote("badge.1")
        open_badges_path = '/dataserver2/OpenBadges/%s' % badge_name
        # pylint: disable=no-member
        testapp = TestApp(self.app)
        res = testapp.get(open_badges_path,
                          extra_environ=self._make_extra_environ(user=username),
                          status=200)

        assert_that(res.json_body, has_entry('Locked', is_(False)))
        assert_that(res.json_body,
                    has_entry('Links', has_item(has_entry('rel', 'lock'))))
        assert_that(res.json_body,
                    has_entry('Links', has_item(has_entry('rel', 'assertion'))))

        export_badge_path = open_badges_path + '/lock'
        res = testapp.post(export_badge_path,
                           extra_environ=self._make_extra_environ(user=username),
                           status=200)

        assert_that(res.json_body, has_entry('Locked', is_(True)))
        assert_that(res.json_body,
                    has_entry('Links', does_not(has_item(has_entry('rel', 'lock')))))
        assert_that(res.json_body,
                    has_entry('Links', has_item(has_entry('rel', 'baked-image'))))
        assert_that(res.json_body,
                    has_entry('Links', has_item(has_entry('rel', 'mozilla-backpack'))))
