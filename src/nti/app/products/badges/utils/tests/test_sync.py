#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import none
from hamcrest import is_not
from hamcrest import assert_that

import os
import shutil
import tempfile
import simplejson

from zope import component

from nti.app.products.badges.tests import NTIBadgesTestCase

from nti.app.products.badges.utils import sync

from nti.badges.interfaces import IBadgeManager

from nti.badges.openbadges.utils.badgebakery import bake_badge

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans


class TestSync(NTIBadgesTestCase):

    @WithMockDSTrans
    def test_sync(self):
        hosted_images = tempfile.mkdtemp(dir="/tmp")
        try:
            # prepare issuer
            issuer_json = os.path.join(os.path.dirname(__file__),
                                       'issuer.json')
            shutil.copy(issuer_json,
                        os.path.join(hosted_images, 'issuer.json'))

            # prepare batch
            badge_json = os.path.join(os.path.dirname(__file__), 'badge.json')
            with open(badge_json, "r") as fp:
                badge = simplejson.load(fp)
                badge['issuer'] = 'file://' + os.path.join(hosted_images, 'issuer.json')

            badge_json = os.path.join(hosted_images, 'badge.json')
            with open(badge_json, "w") as fp:
                simplejson.dump(badge, fp)

            # bake image
            ichigo_png = os.path.join(os.path.dirname(__file__), 'ichigo.png')
            out_ichigo = os.path.join(hosted_images, 'ichigo.png')
            bake_badge(ichigo_png,
                       out_ichigo,
                       'file://' + os.path.join(hosted_images, 'badge.json'))

            sync.sync_db(hosted_images, verify=True)

            badge = None
            issuer = None
            for _, manager in component.getUtilitiesFor(IBadgeManager):
                if issuer is None:
                    issuer = manager.get_issuer(u'Bleach', u"https://bleach.org")
                if badge is None:
                    badge = manager.get_badge('Zangetzus')
            assert_that(badge, is_not(none()))
            assert_that(issuer, is_not(none()))
        finally:
            shutil.rmtree(hosted_images)
