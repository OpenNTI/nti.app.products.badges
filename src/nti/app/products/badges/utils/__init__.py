#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from urllib import quote
from urlparse import urljoin
from urlparse import urlparse

from pyramid.threadlocal import get_current_request

from nti.app.authentication import get_remote_user

from nti.badges.interfaces import IEarnedBadge

from nti.dataserver.users import User
from nti.dataserver.interfaces import IUser

from .. import OPEN_BADGES_VIEW
from .. import HOSTED_BADGE_IMAGES
from .. import OPEN_ASSERTIONS_VIEW

from .. import get_assertion

URL_SCHEMES = ("file", "ftp", "http", "https", "ldap")

def get_user(user=None):
	result = None
	if user is not None:
		result = user if IUser.providedBy(user) else User.get_user(str(user))
	return result

def get_badge_image_url_and_href(context, request=None, user=None):
	image = None
	request = request or get_current_request()
	if not request:
		return (context.image, None)
	
	try:
		ds2 = request.path_info_peek()  # e.g. /dataserver2
	except AttributeError: # in unit test we may see this
		return (context.image, None)
	
	## resolve requesting user
	user = get_user(user)
	
	## href is the open badge URL
	href = '/%s/%s/%s' % (ds2, OPEN_BADGES_VIEW, quote(context.name))
	
	## If it's an earned badge then add make sure
	## we send an image for the assertion
	if 	IEarnedBadge.providedBy(context) and user is not None and \
		get_remote_user() == user:
		## make sure the remote user is the user requesting the assertion
		## to avoid sending it to a wrong person
		assertion = get_assertion(user, context)
		if assertion is not None:
			# add assertion baked image
			uid = quote(assertion.uid)
			href = '/%s/%s/%s/image.png' % (ds2, OPEN_ASSERTIONS_VIEW, uid)
			image = urljoin(request.host_url, href)
			
	if not image:
		## image url fixer
		image = context.image
		scheme = urlparse(image).scheme if image else None
		if not scheme or scheme.lower() not in URL_SCHEMES:
			image = image if image.lower().endswith('.png') else image + '.png'
			image = "%s/%s" % (urljoin(request.host_url, HOSTED_BADGE_IMAGES), image)
	return (image, href)
