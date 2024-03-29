#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import os
import shutil
import tempfile

from zope import component

from nti.app.products.badges.tests import generator

from nti.app.testing.application_webtest import ApplicationTestLayer

from nti.badges.tahrir import manager

from nti.dataserver.tests.mock_dataserver import WithMockDS
from nti.dataserver.tests.mock_dataserver import mock_db_trans
from nti.dataserver.tests.mock_dataserver import DSInjectorMixin

from nti.testing.layers import find_test
from nti.testing.layers import GCLayerMixin
from nti.testing.layers import ZopeComponentLayer
from nti.testing.layers import ConfiguringLayerMixin

import zope.testing.cleanup


def _change_ds_dir(cls):
    cls.old_data_dir = os.getenv('DATASERVER_DATA_DIR')
    cls.new_data_dir = tempfile.mkdtemp(dir="/tmp")
    os.environ['DATASERVER_DATA_DIR'] = cls.new_data_dir


def _restore_ds_dir(cls):
    shutil.rmtree(cls.new_data_dir, True)
    os.environ['DATASERVER_DATA_DIR'] = cls.old_data_dir or '/tmp'


class SharedConfiguringTestLayer(ZopeComponentLayer,
                                 GCLayerMixin,
                                 ConfiguringLayerMixin,
                                 DSInjectorMixin):

    set_up_packages = ('nti.dataserver', 'nti.app.products.badges')

    @classmethod
    def setUp(cls):
        cls.setUpPackages()
        _change_ds_dir(cls)

    @classmethod
    def tearDown(cls):
        cls.tearDownPackages()
        zope.testing.cleanup.cleanUp()
        _restore_ds_dir(cls)

    @classmethod
    def testSetUp(cls, test=None):
        cls.setUpTestDS(test)

    @classmethod
    def testTearDown(cls):
        pass

import unittest


class NTIBadgesTestCase(unittest.TestCase):
    layer = SharedConfiguringTestLayer

sample_size = 5


class NTIBadgesApplicationTestLayer(ApplicationTestLayer):

    @classmethod
    def setUp(cls):
        _change_ds_dir(cls)

    @classmethod
    def tearDown(cls):
        _restore_ds_dir(cls)

    @classmethod
    def testSetUp(cls, unused_test=None):
        bm = manager.create_badge_manager(dburi="sqlite://")
        component.provideUtility(bm)

    @classmethod
    def testTearDown(cls):
        bm = manager.create_badge_manager(defaultSQLite=True)
        component.provideUtility(bm)


class NTISampleBadgesApplicationTestLayer(ApplicationTestLayer):

    @classmethod
    def _register_sample(cls):
        import transaction
        with transaction.manager:
            bm = manager.create_badge_manager(dburi="sqlite://")
            generator.generate_db(bm.db, sample_size, sample_size, sample_size)
            component.provideUtility(bm)

    @classmethod
    def setUp(cls):
        _change_ds_dir(cls)

    @classmethod
    def tearDown(cls):
        _restore_ds_dir(cls)

    @classmethod
    def testSetUp(cls, unused_test=None):
        cls._register_sample()

    @classmethod
    def testTearDown(cls):
        bm = manager.create_badge_manager(dburi="sqlite://")
        component.provideUtility(bm)
