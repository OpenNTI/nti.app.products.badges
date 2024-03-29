#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from six.moves import urllib_parse

from pyramid.threadlocal import get_current_request

from nti.app.products.badges import OPEN_BADGES_VIEW
from nti.app.products.badges import OPEN_ISSUERS_VIEW
from nti.app.products.badges import HOSTED_BADGE_IMAGES
from nti.app.products.badges import OPEN_ASSERTIONS_VIEW

from nti.dataserver.interfaces import IUser

from nti.dataserver.users.users import User

URL_SCHEMES = ("file", "ftp", "http", "https", "ldap")

logger = __import__('logging').getLogger(__name__)


def get_ds2(request=None):
    request = request if request else get_current_request()
    try:
        result = request.path_info_peek() if request else None
    except AttributeError:  # in unit test we may see this
        result = None
    return result or "dataserver2"


def get_user(user=None):
    if user and not IUser.providedBy(user):
        user = User.get_user(str(user))
    return user


def get_badge_href(context, request=None):
    ds2 = get_ds2(request)
    href = '/%s/%s/%s' % (ds2, OPEN_BADGES_VIEW,
                          urllib_parse.quote(context.name))
    return href


def get_badge_url(context, request=None):
    request = request if request else get_current_request()
    href = get_badge_href(context, request=request)
    result = urllib_parse.urljoin(request.host_url, href) if href else href
    return result


def get_badge_image_url(context, request=None):
    image = context.image
    request = request if request else get_current_request()
    if not request:
        return image

    scheme = urllib_parse.urlparse(image).scheme if image else None
    if not scheme or scheme.lower() not in URL_SCHEMES:
        image = image if image.lower().endswith('.png') else image + '.png'
        image = "%s/%s" % (urllib_parse.urljoin(request.host_url,
                                                HOSTED_BADGE_IMAGES), image)
    return image


def get_assertion_url(assertion, request=None, full=False):
    request = request if request else get_current_request()
    ds2 = get_ds2(request)
    uid = urllib_parse.quote(assertion.uid)
    href = '/%s/%s/%s' % (ds2, OPEN_ASSERTIONS_VIEW, uid)
    result = urllib_parse.urljoin(request.host_url, href) if full else href
    return result


def get_assertion_href(assertion, request=None):
    result = get_assertion_url(assertion, request, False)
    return result


def get_assertion_image_url(assertion, request=None, full=True):
    result = get_assertion_url(assertion, request, full)
    if result:
        result += '/image.png'
    return result


def get_assertion_json_url(assertion, request=None, full=True):
    result = get_assertion_url(assertion, request, full)
    if result:
        result += '/assertion.json'
    return result


def get_openbadge_url(context, request=None):
    result = get_badge_url(context, request)
    if result:
        result += "/badge.json"
    return result


def get_issuer_href(context, request=None):
    ds2 = get_ds2(request)
    # href is the open badge URL
    href = '/%s/%s/%s' % (ds2, OPEN_ISSUERS_VIEW, urllib_parse.quote(context.name))
    return href


def get_issuer_url(context, request=None):
    request = request if request else get_current_request()
    href = get_issuer_href(context, request)
    result = urllib_parse.urljoin(request.host_url, href) if href else href
    return result


def get_openissuer_url(context, request=None):
    result = get_issuer_url(context, request)
    if result:
        result += "/issuer.json"
    return result
