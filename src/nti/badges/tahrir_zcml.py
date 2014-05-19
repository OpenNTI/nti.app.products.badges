#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
Directives to be used in ZCML

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import functools

from zope import interface
from zope.configuration import fields
from zope.component.zcml import utility

from . import tahrir_manager
from . import tahrir_interfaces

class IRegisterTahrirDB(interface.Interface):
	"""
	The arguments needed for registering an Tahri db
	"""
	name = fields.TextLine(title="db name identifier (site)", required=False, default="")
	dburi = fields.TextLine(title="db dburi", required=True)

def registerTahrirDB(_context, dburi, name=u""):
	"""
	Register an db
	"""
	factory = functools.partial(tahrir_manager.TahrirBadgeManager, dburi=dburi)
	utility(_context, provides=tahrir_interfaces.ITahrirBadgeManager,
			factory=factory, name=name)
