#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import is_not
from hamcrest import assert_that
does_not = is_not

import fudge

from nti.app.products.badges.utils import get_badge_url
from nti.app.products.badges.utils import get_badge_href
from nti.app.products.badges.utils import get_badge_image_url

from nti.app.products.badges.tests import NTIBadgesTestCase

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
		
		url = get_badge_image_url(badge, request)
		assert_that(url, is_('http://localhost/hosted_badge_images/ichigo.png'))
		
		badge.has_attr(image='http://bleach.org/ichigo.png')
		url = get_badge_image_url(badge, request)
		assert_that(url, is_('http://bleach.org/ichigo.png'))
		
		badge.has_attr(image='tag_nextthought.com_2011-10_OU-HTML-CHEM4970_Chemistry_of_Beer.course_badge.png')
		url = get_badge_image_url(badge, request)
		assert_that(url, is_('http://localhost/hosted_badge_images/tag_nextthought.com_2011-10_OU-HTML-CHEM4970_Chemistry_of_Beer.course_badge.png'))
