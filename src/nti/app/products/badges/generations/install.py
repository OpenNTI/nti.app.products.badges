#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
schema generation installation.

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope.generations.generations import SchemaManager

generation = 4

logger = __import__('logging').getLogger(__name__)


class _NTIBadgesSchemaManager(SchemaManager):
    """
    A schema manager that we can register as a utility in ZCML.
    """

    def __init__(self):
        super(_NTIBadgesSchemaManager, self).__init__(
            generation=generation,
            minimum_generation=generation,
            package_name='nti.app.products.badges.generations')


def evolve(context):
    pass
