#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generation 2.

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import sqlalchemy as sa

from zope import component

from zope.component.hooks import setHooks

from alembic.migration import MigrationContext

from alembic.operations import Operations

from tahrir_api import model
target_metadata = getattr(model.DeclarativeBase, 'metadata')

from nti.badges.tahrir.interfaces import ITahrirBadgeManager

generation = 2

logger = __import__('logging').getLogger(__name__)


def do_evolve(_):
    setHooks()
    manager = component.getUtility(ITahrirBadgeManager)
    if manager.defaultSQLite:
        return
    mc = MigrationContext.configure(manager.engine.connect())
    op = Operations(mc)
    op.add_column("badges", sa.Column('stl', sa.Unicode(128)))


def evolve(context):
    """
    Evolve to generation 2 by adding the stl column to badges
    """
    do_evolve(context)
