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
import time
import simplejson

from zope import component
from zope.catalog.interfaces import ICatalog

from pyramid.view import view_config
from pyramid import httpexceptions as hexc

from nti.app.base.abstract_views import AbstractAuthenticatedView
from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.badges.interfaces import IBadgeManager
from nti.badges.openbadges.interfaces import IBadgeClass

from nti.dataserver.users import User
from nti.dataserver import authorization as nauth
from nti.dataserver.users import index as user_index

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

from nti.utils.maps import CaseInsensitiveDict

from . import get_badge
from . import add_person
from . import add_assertion
from . import person_exists
from . import get_all_badges
from . import assertion_exists
from . import remove_assertion

from .utils.sync import sync_db
from .views import BadgeAdminPathAdapter

class BaseBadgePostView(AbstractAuthenticatedView, 
						ModeledContentUploadRequestUtilsMixin):
	
	def readInput(self, value=None):
		result = CaseInsensitiveDict()
		if self.request.body:
			values = super(BaseBadgePostView, self).readInput(value=value)
			result.update(values)
		return result
	
@view_config(route_name='objects.generic.traversal',
			 name='award',
			 renderer='rest',
			 request_method='POST',
			 context=BadgeAdminPathAdapter,
			 permission=nauth.ACT_MODERATE)
class AwardBadgeView(BaseBadgePostView):
	
	def __call__(self):
		vls = self.readInput()
		username = vls.get('username') or vls.get('email') or self.remoteUser.username
		user = User.get_user(username)
		if user is None:
			ent_catalog = component.getUtility(ICatalog, name=user_index.CATALOG_NAME)
			results = list(ent_catalog.searchResults(email=(username, username)))
			user = results[0] if results else None
		if user is None:
			raise hexc.HTTPUnprocessableEntity('User not found')
		
		for name in ('badge', 'badge_name', 'badgeName', 'badgeid', 'badge_id'):
			badge_name = vls.get(name)
			if badge_name:
				break
		if not badge_name:
			raise hexc.HTTPUnprocessableEntity('Badge name was not specified')
	
		badge = get_badge(badge_name)
		if badge is None:
			raise hexc.HTTPNotFound('Badge not found')
	
		# add person if required
		# an adapter must exists to convert the user to a person
		if not person_exists(user):
			add_person(user)
	
		# add assertion
		if not assertion_exists(user, badge_name):
			add_assertion(user, badge_name)
			logger.info("Badge '%s' added to user %s", badge_name, username)
	
		return hexc.HTTPNoContent()

@view_config(route_name='objects.generic.traversal',
			 name='revoke',
			 renderer='rest',
			 request_method='POST',
			 context=BadgeAdminPathAdapter,
			 permission=nauth.ACT_MODERATE)
class RevokeBadgeView(BaseBadgePostView):
	
	def __call__(self):
		vls = self.readInput()
		username = vls.get('username') or vls.get('email') or self.remoteUser.username
		user = User.get_user(username)
		if user is None:
			ent_catalog = component.getUtility(ICatalog, name=user_index.CATALOG_NAME)
			results = list(ent_catalog.searchResults(email=(username, username)))
			user = results[0] if results else None
		if user is None:
			raise hexc.HTTPNotFound('User not found')
	
		for name in ('badge', 'badge_name', 'badgeName', 'badgeid', 'badge_id'):
			badge_name = vls.get(name)
			if badge_name:
				break
		if not badge_name:
			raise hexc.HTTPUnprocessableEntity('Badge name was not specified')
	
		manager = component.getUtility(IBadgeManager)
		badge = manager.get_badge(badge_name)
		if badge is None:
			raise hexc.HTTPNotFound('Badge not found')
	
		if manager.assertion_exists(user, badge_name):
			manager.remove_assertion(user, badge_name)
			logger.info("Badge '%s' revoked from user %s", badge_name, username)
		else:
			logger.warn('Assertion (%s,%s) not found', user, badge_name)
	
		return hexc.HTTPNoContent()

@view_config(route_name='objects.generic.traversal',
			 name='sync_db',
			 renderer='rest',
			 request_method='POST',
			 context=BadgeAdminPathAdapter,
			 permission=nauth.ACT_MODERATE)
class SyncDbView(BaseBadgePostView):

	def __call__(self):
		values = self.readInput()
	
		# get badge directory
		for name in ('directory', 'dir', 'path', 'hosted_badge_images'):
			directory = values.get(name)
			if directory:
				break
	
		if not directory:
			directory = os.getenv('HOSTED_BADGE_IMAGES_DIR')
	
		if not directory or not os.path.exists(directory) or not os.path.isdir(directory):
			raise hexc.HTTPNotFound('Directory not found')
	
		# update badges
		update = values.get('update') or u''
		update = str(update).lower() in ('1', 'true', 't', 'yes', 'y', 'on')
	
		# verify object
		verify = values.get('verify') or u''
		verify = str(verify).lower() in ('1', 'true', 't', 'yes', 'y', 'on')
	
		secret = values.get('secret')
		now = time.time()
	
		# sync database
		issuers, badges = sync_db(directory, update=update, verify=verify, secret=secret)
	
		# return
		result = LocatedExternalDict()
		result['Badges'] = badges
		result['Issuers'] = issuers
		result['Elapsed'] = time.time() - now
		return result

def bulk_import(input_source, errors=[]):
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

		badge = get_badge(badge_name)
		if badge is None:
			errors.append("Invalid badge '%s' in line %s" % (badge_name, line))
			continue

		if operation == 'award' and not assertion_exists(user, badge_name):
			awards += 1
			add_assertion(user, badge_name)
			logger.info('Badge %s awarded to %s', badge_name, username)
		elif operation == 'revoke' and assertion_exists(user, badge_name):
			revokations += 1
			remove_assertion(user, badge_name)
			logger.info('Badge %s revoked from %s', badge_name, username)

	return (awards, revokations)

@view_config(route_name='objects.generic.traversal',
			 name='bulk_import',
			 renderer='rest',
			 request_method='POST',
			 context=BadgeAdminPathAdapter,
			 permission=nauth.ACT_MODERATE)
class BulkImportView(AbstractAuthenticatedView):
	
	def __call__(self):
		now = time.time()
		request = self.request
		result = LocatedExternalDict()
		result['Errors'] = errors = []
		if request.POST:
			values = CaseInsensitiveDict(request.POST)
			source=values['source'].file
			source.seek(0)
		else:
			values = simplejson.loads(unicode(request.body, request.charset))
			values = CaseInsensitiveDict(values)
			source = os.path.expanduser(values['source'])
			source = open(source, "r")
	
		awards, revokations = bulk_import(source, errors)
		result['Awards'] = awards
		result['Revokations'] = revokations
		result['Elapsed'] = time.time() - now
		return result

@view_config(route_name='objects.generic.traversal',
			 name='AllBadges',
			 renderer='rest',
			 request_method='GET',
			 context=BadgeAdminPathAdapter,
			 permission=nauth.ACT_MODERATE)
class AllBadgesView(object):

	def __init__(self, request):
		self.request = request

	def __call__(self):
		result = LocatedExternalDict()
		result[StandardExternalFields.ITEMS] = items = []
		items.extend(IBadgeClass(x) for x in get_all_badges())
		result['Total'] = len(items)
		return result
