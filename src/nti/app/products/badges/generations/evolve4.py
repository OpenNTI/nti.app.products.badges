#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generation 4.

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import datetime
import sqlalchemy as sa

from zope import component

from zope.component.hooks import setHooks

from sqlalchemy import inspect

from alembic.migration import MigrationContext

from alembic.operations import Operations

from tahrir_api import model
target_metadata = getattr(model.DeclarativeBase, 'metadata')

try:
    from tahrir_api.model import generate_default_id
except ImportError:
    def generate_default_id(context):
        return context.current_parameters['name'].lower().replace(' ', '-')

from nti.app.products.badges.generations import table_exists

from nti.badges.tahrir.interfaces import ITahrirBadgeManager

generation = 4

logger = __import__('logging').getLogger(__name__)


def upgrade(op):
    op.create_table(
        'team',
        sa.Column('id', sa.Unicode(128), primary_key=True,
                  default=generate_default_id),
        sa.Column('name', sa.Unicode(128), nullable=False, unique=True),
        sa.Column('created_on', sa.DateTime(), nullable=False,
                  default=datetime.datetime.utcnow),
    )

    op.create_table(
        'series',
        sa.Column('id', sa.Unicode(128), primary_key=True,
                  default=generate_default_id),
        sa.Column('name', sa.Unicode(128), nullable=False, unique=True),
        sa.Column('description', sa.Unicode(128), nullable=False),
        sa.Column('created_on', sa.DateTime(), nullable=False,
                  default=datetime.datetime.utcnow),
        sa.Column('last_updated', sa.DateTime(), nullable=False,
                  default=datetime.datetime.utcnow,
                  onupdate=datetime.datetime.utcnow),
        sa.Column('tags', sa.Unicode(128)),
        sa.Column('team_id', sa.Unicode(128), sa.ForeignKey('team.id'),
                  nullable=False),
    )

    op.create_table(
        'milestone',
        sa.Column('id', sa.Integer(), primary_key=True, unique=True),
        sa.Column('position', sa.Integer(), default=None),
        sa.Column('badge_id', sa.Unicode(128),
                  sa.ForeignKey('badges.id'), nullable=False),
        sa.Column('series_id', sa.Unicode(128),
                  sa.ForeignKey('series.id'), nullable=False),
    )
    op.create_unique_constraint('milestone_unique_constraint', 'milestone',
                                ['position', 'badge_id', 'series_id'])


def downgrade(op):
    op.drop_table('milestone')
    op.drop_table('series')
    op.drop_table('team')


def do_evolve(_):
    setHooks()
    manager = component.getUtility(ITahrirBadgeManager)
    if manager.defaultSQLite or manager.engine.name == 'sqlite':
        return

    connection = manager.engine.connect()
    mc = MigrationContext.configure(connection)
    op = Operations(mc)
    inspector = inspect(manager.engine)

    if not table_exists(inspector, 'team'):
        upgrade(op)
    logger.info('Finished badge evolve (%s)', generation)


def evolve(context):
    """
    Evolve to generation 4 by adding new team, series and milestone tables
    """
    do_evolve(context)
