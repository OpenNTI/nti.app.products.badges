#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generation 3.

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

generation = 3

logger = __import__('logging').getLogger(__name__)


def do_evolve(_):
    setHooks()
    manager = component.getUtility(ITahrirBadgeManager)
    if manager.defaultSQLite:
        return
    mc = MigrationContext.configure(manager.engine.connect())
    op = Operations(mc)
    op.add_column("assertions", sa.Column('exported', sa.Boolean(),
                                          nullable=True, unique=False))


def evolve(context):
    """
    Evolve to generation 3 by adding the exported column to assertions table
    """
    do_evolve(context)
