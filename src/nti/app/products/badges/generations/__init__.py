#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


def get_column_names(column_infos):
    return [x['name'] for x in column_infos]


def column_exists(inspector, table, column):
    return column in get_column_names(inspector.get_columns(table))


def table_exists(inspector, table):
    return table in inspector.get_table_names()
