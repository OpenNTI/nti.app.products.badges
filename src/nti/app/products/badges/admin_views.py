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

from pyramid.view import view_config
from pyramid import httpexceptions as hexc

from nti.badges import interfaces as badges_interfaces

from nti.dataserver.users import User
from nti.dataserver import authorization as nauth
from nti.dataserver import interfaces as nti_interfaces

from nti.externalization.interfaces import LocatedExternalDict

from nti.utils.maps import CaseInsensitiveDict

from . import utils
from . import views
from . import interfaces
from . import get_user_id
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
			ntiperson = badges_interfaces.INTIPerson(user)
			if not manager.person_exists(ntiperson):
				ntiperson.createdTime = time.time()
				if manager.add_person(ntiperson):
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
		raise hexc.HTTPNotFound('User not found')
	
	badge = None
	badge_name = values.get('badge', values.get('badge_name', values.get('badgeName')))
	for manager in get_user_badge_managers(user):
		badge = manager.get_badge(badge_name)
		if badge is not None:
			break

	if badge is None:
		raise hexc.HTTPNotFound('Badge not found')

	predicate = interfaces.get_badge_predicate_for_user(user)
	if not predicate(badge):
		raise hexc.HTTPForbidden("Badge not authorized")

	# add person if required
	# an adapter must exists to convert the user to a person
	manager.add_person(user)

	# add assertion
	uid = get_user_id(user)
	manager.add_assertion(uid, badge_name)

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
		raise hexc.HTTPNotFound('User not found')

	badge = None
	badge_name = values.get('badge', values.get('badge_name', values.get('badgeName')))
	for manager in get_user_badge_managers(user):
		badge = manager.get_badge(badge_name)
		if badge is not None:
			break

	if badge is None:
		raise hexc.HTTPNotFound('Badge not found')

	uid = get_user_id(user)
	if manager.assertion_exists(uid, badge_name):
		manager.remove_assertion(uid, badge_name)
	else:
		logger.debug('Assertion (%s,%s) not found', uid, badge_name)

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
	directory = values.get('directory')
	if not directory or not os.path.exists(directory) or not os.path.isdir(directory):
		raise hexc.HTTPNotFound('Directory not found')

	# get database name
	dbname = values.get('dbid', values.get('db_id',
					  values.get('dbname'), values.get('db_name')))

	# verify object
	verify = values.get('verify') or u''
	verify = str(verify).lower() in ('1', 'true', 't', 'yes', 'y', 'on')

	now = time.time()
	# sync database
	utils.sync.sync_db(directory, dbname, verify)

	# return
	result = LocatedExternalDict()
	result['Elapsed'] = time.time() - now
	return result
