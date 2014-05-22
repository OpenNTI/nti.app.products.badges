#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
admin views.

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
import time
import simplejson

from zope import component

from pyramid.view import view_config

from nti.badges import interfaces as badges_interfaces

from nti.dataserver.users import User
from nti.dataserver import authorization as nauth
from nti.dataserver import interfaces as nti_interfaces

from nti.externalization.interfaces import LocatedExternalDict

from nti.utils.maps import CaseInsensitiveDict

from . import views
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
			 context=views.BadgesPathAdapter,
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
			uid = get_user_id(user)
			if not manager.person_exists(pid=uid, name=user.username):
				ntiperson = badges_interfaces.INTIPerson(user)
				ntiperson.createdTime = time.time()
				if manager.add_person(ntiperson):
					total += 1

	result = LocatedExternalDict()
	result['Elapsed'] = time.time() - now
	result['Total'] = total
	return result
