#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
admin views.

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import six
import time
import simplejson

from zope import component
from zope.catalog.interfaces import ICatalog

from pyramid.view import view_config
from pyramid import httpexceptions as hexc

from nti.dataserver.users import User
from nti.dataserver import authorization as nauth
from nti.dataserver.users import index as user_index
from nti.dataserver import interfaces as nti_interfaces

from nti.externalization.interfaces import LocatedExternalDict

from nti.utils.maps import CaseInsensitiveDict

from .utils import sync

from . import views
from . import get_user_id
from . import get_manager_and_badge
from . import get_user_badge_managers

def _make_min_max_btree_range(search_term):
	min_inclusive = search_term  # start here
	max_exclusive = search_term[0:-1] + unichr(ord(search_term[-1]) + 1)
	return min_inclusive, max_exclusive

def username_search(search_term):
	min_inclusive, max_exclusive = _make_min_max_btree_range(search_term)
	dataserver = component.getUtility(nti_interfaces.IDataserver)
	_users = nti_interfaces.IShardLayout(dataserver).users_folder
	usernames = list(_users.iterkeys(min_inclusive, max_exclusive, excludemax=True))
	return usernames

def readInput(request):
	body = request.body
	result = CaseInsensitiveDict()
	if body:
		try:
			values = simplejson.loads(unicode(body, request.charset))
		except UnicodeError:
			values = simplejson.loads(unicode(body, 'iso-8859-1'))
		result.update(**values)
	return result

@view_config(route_name='objects.generic.traversal',
			 name='create_persons',
			 renderer='rest',
			 request_method='POST',
			 context=views.BadgeAdminPathAdapter,
			 permission=nauth.ACT_MODERATE)
def create_persons(request):
	values = readInput(request)
	usernames = values.get('usernames')
	term = values.get('term', values.get('search', None))
	if term:
		usernames = username_search(term)
	elif usernames and isinstance(usernames, six.string_types):
		usernames = usernames.split(',')
	else:
		dataserver = component.getUtility(nti_interfaces.IDataserver)
		_users = nti_interfaces.IShardLayout(dataserver).users_folder
		usernames = _users.keys()

	total = 0
	now = time.time()
	for username in usernames:
		user = User.get_user(username.lower())
		if not user or not nti_interfaces.IUser.providedBy(user):
			continue
		for manager in get_user_badge_managers(user):
			if not manager.person_exists(user):
				if manager.add_person(user):
					total += 1

	result = LocatedExternalDict()
	result['Total'] = total
	result['Elapsed'] = time.time() - now
	return result

@view_config(route_name='objects.generic.traversal',
			 name='award',
			 renderer='rest',
			 request_method='POST',
			 context=views.BadgeAdminPathAdapter,
			 permission=nauth.ACT_MODERATE)
def award(request):
	values = readInput(request)
	username = values.get('username', request.authenticated_userid)
	user = User.get_user(username)
	if user is None:
		ent_catalog = component.getUtility(ICatalog, name=user_index.CATALOG_NAME)
		results = list(ent_catalog.searchResults(email=(username, username)))
		user = results[0] if results else None
	if user is None:
		raise hexc.HTTPNotFound('User not found')
	
	for name in ('badge', 'badge_name', 'badgeName', 'badgeid', 'badge_id'):
		badge_name = values.get(name)
		if badge_name:
			break
	if not badge_name:
		raise hexc.HTTPUnprocessableEntity('Badge name was not specified')

	manager, badge = get_manager_and_badge(badge_name)
	if badge is None:
		raise hexc.HTTPNotFound('Badge not found')

	# add person if required
	# an adapter must exists to convert the user to a person
	manager.add_person(user)

	# add assertion
	uid = get_user_id(user)
	if not manager.assertion_exists(uid, badge_name):
		manager.add_assertion(uid, badge_name)
		logger.info("Badge '%s' added to user %s", badge_name, username)

	return hexc.HTTPNoContent()

@view_config(route_name='objects.generic.traversal',
			 name='revoke',
			 renderer='rest',
			 request_method='POST',
			 context=views.BadgeAdminPathAdapter,
			 permission=nauth.ACT_MODERATE)
def revoke(request):
	values = readInput(request)
	username = values.get('username', request.authenticated_userid)
	user = User.get_user(username)
	if user is None:
		ent_catalog = component.getUtility(ICatalog, name=user_index.CATALOG_NAME)
		results = list(ent_catalog.searchResults(email=(username, username)))
		user = results[0] if results else None
	if user is None:
		raise hexc.HTTPNotFound('User not found')

	for name in ('badge', 'badge_name', 'badgeName', 'badgeid', 'badge_id'):
		badge_name = values.get(name)
		if badge_name:
			break
	if not badge_name:
		raise hexc.HTTPUnprocessableEntity('Badge name was not specified')

	manager, badge = get_manager_and_badge(badge_name)
	if badge is None:
		raise hexc.HTTPNotFound('Badge not found')

	uid = get_user_id(user)
	if manager.assertion_exists(uid, badge_name):
		manager.remove_assertion(uid, badge_name)
		logger.info("Badge '%s' revoked from user %s", badge_name, username)
	else:
		logger.warn('Assertion (%s,%s) not found', uid, badge_name)

	return hexc.HTTPNoContent()

@view_config(route_name='objects.generic.traversal',
			 name='sync_db',
			 renderer='rest',
			 request_method='POST',
			 context=views.BadgeAdminPathAdapter,
			 permission=nauth.ACT_MODERATE)
def sync_db(request):
	values = readInput(request)

	# get badge directory
	for name in ('directory', 'dir', 'path', 'hosted_badge_images'):
		directory = values.get(name)
		if directory:
			break

	if not directory:
		directory = os.getenv('HOSTED_BADGE_IMAGES_DIR')

	if not directory or not os.path.exists(directory) or not os.path.isdir(directory):
		raise hexc.HTTPNotFound('Directory not found')

	# get database name
	for name in ('dbid', 'dbname', 'db_id', 'db_name'):
		dbname = values.get(name)

	# verify object
	verify = values.get('verify') or u''
	verify = str(verify).lower() in ('1', 'true', 't', 'yes', 'y', 'on')

	secret = values.get('secret')
	now = time.time()

	# sync database
	issuers, badges = sync.sync_db(directory, dbid=dbname, verify=verify, secret=secret)

	# return
	result = LocatedExternalDict()
	result['BadgesAdded'] = badges
	result['IssuersAdded'] = issuers
	result['Elapsed'] = time.time() - now
	return result

def bulk_import(input_source, errors=[]):
	managers = {}
	ent_catalog = component.getUtility(ICatalog, name=user_index.CATALOG_NAME)

	awards = 0
	revokations = 0
	for line, source in enumerate(input_source):
		line += 1
		source = source.strip()
		if not source or source.startswith("#"):
			continue
		splits = source.split('\t')
		if len(splits) < 2:
			errors.append("Incorrect input in line %s" % line)
			continue

		username, badge_name = splits[0].lower(), splits[1]
		operation = splits[2].lower() if len(splits) >= 3 else 'award'
		if operation not in ('award', 'revoke'):
			errors.append("Invalid operation '%s' in line %s" % (operation, line))
			continue

		user = User.get_user(username)
		if user is None:
			results = list(ent_catalog.searchResults(email=(username, username)))
			user = results[0] if results else None
		if user is None:
			errors.append("Invalid user '%s' in line %s" % (username, line))
			continue

		manager = managers.get(badge_name)
		if manager is None:
			manager, _ = get_manager_and_badge(badge_name)
			if manager is None:
				errors.append("Invalid badge '%s' in line %s" % (badge_name, line))
				continue
			managers[badge_name] = manager

		uid = get_user_id(user)
		if operation == 'award' and not manager.assertion_exists(uid, badge_name):
			awards += 1
			manager.add_assertion(uid, badge_name)
			logger.info('Badge %s awarded to %s', badge_name, username)
		elif operation == 'revoke' and manager.assertion_exists(uid, badge_name):
			revokations += 1
			manager.remove_assertion(uid, badge_name)
			logger.info('Badge %s revoked from %s', badge_name, username)

	return (awards, revokations)

@view_config(route_name='objects.generic.traversal',
			 name='bulk_import',
			 renderer='rest',
			 request_method='POST',
			 context=views.BadgeAdminPathAdapter,
			 permission=nauth.ACT_MODERATE)
def bulk_import_view(request):
	now = time.time()
	result = LocatedExternalDict()
	result['Errors'] = errors = []
	source = request.POST['source'].file
	source.seek(0)
	awards, revokations = bulk_import(source, errors)
	result['Awards'] = awards
	result['Revokations'] = revokations
	result['Elapsed'] = time.time() - now
	return result
