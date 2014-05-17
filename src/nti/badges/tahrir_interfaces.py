#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

from zope import interface

from nti.utils import schema as nti_schema

from . import interfaces

class IIssuer(interface.Interface):
	id = nti_schema.ValidTextLine(title=" Issuer id")
	origin = nti_schema.ValidTextLine(title=" Issuer origin")
	name = nti_schema.ValidTextLine(title=" Issuer name")
	org = nti_schema.ValidTextLine(title=" Issuer organization")
	contact = nti_schema.ValidTextLine(title=" Issuer contact")
	created_on =  nti_schema.ValidDatetime(title="Created time")

class ITahrirBadgeManager(interfaces.IBadgeManager):
	"""
	Interface for Tahrir database managers
	"""
