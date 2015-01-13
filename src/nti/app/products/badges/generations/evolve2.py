#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generation 2.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 2

import sqlalchemy as sa

from zope import component
from zope.component.hooks import setHooks

from alembic.operations import Operations
from alembic.migration import MigrationContext

from tahrir_api import model
target_metadata = getattr(model.DeclarativeBase, 'metadata')

from nti.badges.tahrir.interfaces import ITahrirBadgeManager

def do_evolve(dscontext):
	setHooks()
	
	manager = component.getUtility(ITahrirBadgeManager)
	mc = MigrationContext.configure(manager.engine.connect())
	op = Operations(mc)
	op.add_column("badges", sa.Column('stl', sa.Unicode(128)))

def evolve(context):
	"""
	Evolve to generation 2 by adding the stl column
	"""
	do_evolve(context)
