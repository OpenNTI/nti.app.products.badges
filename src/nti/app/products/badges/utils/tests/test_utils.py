#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import is_not
from hamcrest import assert_that
does_not = is_not

import fudge

from nti.app.products.badges.tests import NTIBadgesTestCase

from nti.app.products.badges.utils import get_badge_url
from nti.app.products.badges.utils import get_badge_href
from nti.app.products.badges.utils import get_openbadge_url
from nti.app.products.badges.utils import get_badge_image_url

from nti.app.products.badges.utils import get_assertion_url


class TestUtils(NTIBadgesTestCase):

    def _mock_request(self):
        result = fudge.Fake()
        result.provides('path_info_peek').returns("dataserver2")
        result.has_attr(host_url='http://localhost')
        return result

    def test_get_badge_urls(self):
        request = self._mock_request()
        badge = fudge.Fake()
        badge.has_attr(name='ichigo')
        badge.has_attr(image='ichigo.png')

        href = get_badge_href(badge, request)
        assert_that(href, is_('/dataserver2/OpenBadges/ichigo'))

        url = get_badge_url(badge, request)
        assert_that(url, is_('http://localhost/dataserver2/OpenBadges/ichigo'))

        url = get_openbadge_url(badge, request)
        assert_that(url,
                    is_('http://localhost/dataserver2/OpenBadges/ichigo/badge.json'))

        url = get_badge_image_url(badge, request)
        assert_that(url,
                    is_('http://localhost/hosted_badge_images/ichigo.png'))

        badge.has_attr(image='http://bleach.org/ichigo.png')
        url = get_badge_image_url(badge, request)
        assert_that(url, is_('http://bleach.org/ichigo.png'))

        image = 'tag_nextthought.com_2011-10_OU-HTML-CHEM4970_Chemistry_of_Beer.course_badge.png'
        badge.has_attr(image=image)
        url = get_badge_image_url(badge, request)
        assert_that(url,
                    is_('http://localhost/hosted_badge_images/tag_nextthought.com_2011-10_OU-HTML-CHEM4970_Chemistry_of_Beer.course_badge.png'))

    def test_get_assertion_urls(self):
        request = self._mock_request()
        assertion = fudge.Fake()
        assertion.has_attr(uid='xy##%6')

        href = get_assertion_url(assertion, request)
        assert_that(href, is_('/dataserver2/OpenAssertions/xy%23%23%256'))

        href = get_assertion_url(assertion, request, True)
        assert_that(href,
                    is_('http://localhost/dataserver2/OpenAssertions/xy%23%23%256'))
