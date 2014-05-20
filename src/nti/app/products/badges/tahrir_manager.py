#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six

from zope import interface
from zope import component

from pyramid.threadlocal import get_current_request

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from zope.sqlalchemy import ZopeTransactionExtension

from tahrir_api.dbapi import TahrirDatabase
from tahrir_api.model import DeclarativeBase as tahrir_base

from nti.utils.property import Lazy

from . import tahrir_interfaces

def get_possible_site_names(request=None, include_default=True):
	request = request or get_current_request()
	if not request:
		return () if not include_default else ('',)
	__traceback_info__ = request

	site_names = getattr(request, 'possible_site_names', ())
	if include_default:
		site_names += ('',)
	return site_names

def get_tahri_badgemanger(names=None, request=None):
	names = names.split() if isinstance(names, six.string_types) else names
	names = names or get_possible_site_names(request=request)
	for site in names:
		manager = component.queryUtility(tahrir_interfaces.ITahrirBadgeManager, name=site)
		if manager is not None:
			return manager
	return None

class NTITahrirDatabase(TahrirDatabase):
	pass

@interface.implementer(tahrir_interfaces.ITahrirBadgeManager)
class TahrirBadgeManager(object):

	def __init__(self, dburi, twophase=False, autocommit=True):
		self.dburi = dburi
		self.twophase = twophase
		self.autocommit = autocommit

	@Lazy
	def engine(self):
		result = create_engine(self.dburi)
		return result

	@Lazy
	def sessionmaker(self):
		result = sessionmaker(bind=self.engine,
							  twophase=self.twophase,
							  extension=ZopeTransactionExtension())
		return result

	@Lazy
	def session(self):
		result = scoped_session(self.sessionmaker)
		return result

	@Lazy
	def db(self):
		result = NTITahrirDatabase(session=self.session, autocommit=self.autocommit)
		self.session.configure(bind=self.engine)
		metadata = getattr(tahrir_base, 'metadata')
		metadata.create_all(self.engine, checkfirst=True)
		return result

def create_tahrir_badge_manager(dburi, twophase=False, autocommit=True):
	result = TahrirBadgeManager(dburi, twophase, autocommit)
	return result
