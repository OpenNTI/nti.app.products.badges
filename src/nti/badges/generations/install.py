# -*- coding: utf-8 -*-
"""
schema generation installation.

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 1

from zope.generations.generations import SchemaManager

class _NTIBadgesSchemaManager(SchemaManager):
	"""
	A schema manager that we can register as a utility in ZCML.
	"""
	def __init__(self):
		super(_NTIBadgesSchemaManager, self).__init__(
												generation=generation,
												minimum_generation=generation,
												package_name='nti.badges.generations')
def evolve(context):
	pass
