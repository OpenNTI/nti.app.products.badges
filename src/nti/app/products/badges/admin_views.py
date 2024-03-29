#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import time

from pyramid import httpexceptions as hexc

from pyramid.view import view_config
from pyramid.view import view_defaults

from requests.structures import CaseInsensitiveDict

from zope import component

from zope.event import notify

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.error import raise_json_error

from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.products.badges import MessageFactory as _

from nti.app.products.badges import get_badge
from nti.app.products.badges import add_person
from nti.app.products.badges import add_assertion
from nti.app.products.badges import get_assertion
from nti.app.products.badges import person_exists
from nti.app.products.badges import get_all_badges
from nti.app.products.badges import assertion_exists
from nti.app.products.badges import remove_assertion

from nti.app.products.badges.utils.sync import sync_db

from nti.app.products.badges.views import BadgeAdminPathAdapter

from nti.badges.interfaces import IBadgeManager

from nti.badges.openbadges.interfaces import IBadgeClass
from nti.badges.openbadges.interfaces import IBadgeAssertion
from nti.badges.openbadges.interfaces import BadgeAwardedEvent

from nti.common.string import is_true

from nti.dataserver import authorization as nauth

from nti.dataserver.users.interfaces import IUserProfile

from nti.dataserver.users.users import User

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

ITEMS = StandardExternalFields.ITEMS
TOTAL = StandardExternalFields.TOTAL
ITEM_COUNT = StandardExternalFields.ITEM_COUNT

logger = __import__('logging').getLogger(__name__)


class BaseBadgePostView(AbstractAuthenticatedView,
                        ModeledContentUploadRequestUtilsMixin):

    def readInput(self, value=None):
        result = CaseInsensitiveDict()
        if self.request.body:
            values = super(BaseBadgePostView, self).readInput(value)
            result.update(values)
        return result


@view_config(name='award')
@view_config(name='Award')
@view_config(name='award_badge')
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               request_method='POST',
               context=BadgeAdminPathAdapter,
               permission=nauth.ACT_NTI_ADMIN)
class AwardBadgeView(BaseBadgePostView):

    def __call__(self):
        values = self.readInput()

        # validate user
        username = values.get('user') \
                or values.get('email') \
                or values.get('username')
        if not username:
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(u"Username was not specified."),
                                 'code': 'UsernameNotSpecified',
                             },
                             None)

        user = User.get_user(username)
        if user is None:
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(u"User not found."),
                                 'code': 'UserNotFound',
                             },
                             None)

        # validate badge
        for name in ('badge', 'badge_name', 'badgeName', 'badgeid', 'badge_id'):
            badge_name = values.get(name)
            if badge_name:
                break
        if not badge_name:
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(u"Badge name was not specified."),
                                 'code': 'BadgenameNotSpecified',
                             },
                             None)

        badge = get_badge(badge_name)
        if badge is None:
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(u"Badge name not found."),
                                 'code': 'BadgenameNotFound',
                             },
                             None)

        # add person if required
        # an adapter must exists to convert the user to a person
        if not person_exists(user):
            add_person(user)

        # add assertion
        result = get_assertion(user, badge_name)
        if result is None:
            add_assertion(user, badge_name)
            result = get_assertion(user, badge_name)
            notify(BadgeAwardedEvent(result, self.remoteUser))
            logger.info("Badge '%s' added to user %s",
                        badge_name, username)
        result = IBadgeAssertion(result)
        return result


@view_config(name='revoke')
@view_config(name='Revoke')
@view_config(name='revoke_badge')
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               request_method='POST',
               context=BadgeAdminPathAdapter,
               permission=nauth.ACT_NTI_ADMIN)
class RevokeBadgeView(BaseBadgePostView):

    def __call__(self):
        values = self.readInput()

        # validate user
        username = values.get('user') \
                or values.get('username') \
                or values.get('email')
        if not username:
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(u"Username was not specified."),
                                 'code': 'UsernameNotSpecified',
                             },
                             None)
        user = User.get_user(username)
        if user is None:
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(u"User not found."),
                                 'code': 'UserNotFound',
                             },
                             None)

        # validate badge
        for name in ('badge', 'name'):
            badge_name = values.get(name)
            if badge_name:
                break
        if not badge_name:
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(u"Badge name was not specified."),
                                 'code': 'BadgenameNotSpecified',
                             },
                             None)

        manager = component.getUtility(IBadgeManager)
        badge = manager.get_badge(badge_name)
        if badge is None:
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(u"Badge name not found."),
                                 'code': 'BadgenameNotFound',
                             },
                             None)

        if manager.assertion_exists(user, badge_name):
            manager.remove_assertion(user, badge_name)
            logger.info("Badge '%s' revoked from user %s",
                        badge_name, username)
        else:
            logger.warn('Assertion (%s,%s) not found', user, badge_name)
            raise hexc.HTTPNotFound()

        return hexc.HTTPNoContent()


@view_config(name='SyncDb')
@view_config(name='sync_db')
@view_config(name='sync_badges')
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               request_method='POST',
               context=BadgeAdminPathAdapter,
               permission=nauth.ACT_NTI_ADMIN)
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

        if     not directory or not os.path.exists(directory) \
            or not os.path.isdir(directory):
            raise hexc.HTTPNotFound(_("Directory not found."))

        # update badges
        update = is_true(values.get('update'))

        # verify object
        verify = is_true(values.get('verify'))

        secret = values.get('secret')
        now = time.time()

        # sync database
        issuers, badges = sync_db(directory,
                                  update=update,
                                  verify=verify,
                                  secret=secret)

        # return
        result = LocatedExternalDict()
        result['Badges'] = badges
        result['Issuers'] = issuers
        result['Elapsed'] = time.time() - now
        return result


def bulk_import(input_source, errors=None):
    awards = 0
    revokations = 0
    errors = [] if errors is None else errors
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
            errors.append("Invalid operation '%s' in line %s" %
                          (operation, line))
            continue

        user = User.get_user(username)
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


@view_config(name='BulkImport')
@view_config(name='bulk_import')
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               request_method='POST',
               context=BadgeAdminPathAdapter,
               permission=nauth.ACT_NTI_ADMIN)
class BulkImportView(AbstractAuthenticatedView,
                     ModeledContentUploadRequestUtilsMixin):

    def __call__(self):
        now = time.time()
        request = self.request
        result = LocatedExternalDict()
        result['Errors'] = errors = []
        if request.POST:
            values = CaseInsensitiveDict(request.POST)
            source = values['source'].file
            source.seek(0)
        else:
            values = self.readInput()
            values = CaseInsensitiveDict(values)
            source = os.path.expanduser(values['source'])
            source = open(source, "r")

        awards, revokations = bulk_import(source, errors)
        result['Awards'] = awards
        result['Revokations'] = revokations
        result['Elapsed'] = time.time() - now
        return result


@view_config(name='UpdatePersons')
@view_config(name='update_persons')
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               request_method='POST',
               context=BadgeAdminPathAdapter,
               permission=nauth.ACT_NTI_ADMIN)
class UpdatePersonsView(AbstractAuthenticatedView):

    def check(self, s):
        return u'' if not s else s.lower()

    def get_user(self, person):
        username = person.nickname
        return User.get_user(username)

    def update_person(self, manager, person, messages, errors):
        user = self.get_user(person)
        if user is None:
            errors.append("User %s could not be found" % person.nickname)
            return False

        result = False
        profile = IUserProfile(user, None)
        username = self.check(user.username)

        # check email
        email = self.check(getattr(profile, "email", u'')) or username
        email_verified = getattr(profile, "email_verified", False)
        if email_verified and email != self.check(person.email):
            result = True
            messages.append("Email updated for person %s" % person.nickname)

        # check other fields
        bio = getattr(profile, 'about', None) or u''
        website = getattr(profile, 'home_page', None) or u''

        result = result or (bio != person.bio)
        result = result or (website != person.website)
        if result:
            manager.update_person(person,
                                  email=email,
                                  name=username,
                                  website=website,
                                  bio=bio)
        return result

    def __call__(self):
        count = 0
        now = time.time()
        result = LocatedExternalDict()
        result['Errors'] = errors = []
        result['Messages'] = messages = []
        manager = component.getUtility(IBadgeManager)
        for person in manager.get_all_persons():
            if self.update_person(manager, person, messages, errors):
                count += 1
        result['Elapsed'] = time.time() - now
        result[ITEM_COUNT] = result[TOTAL] = count
        return result


@view_config(name='AllBadges')
@view_config(name='all_badges')
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               request_method='GET',
               context=BadgeAdminPathAdapter,
               permission=nauth.ACT_NTI_ADMIN)
class AllBadgesView(object):

    def __init__(self, request):
        self.request = request

    def __call__(self):
        result = LocatedExternalDict()
        result[ITEMS] = items = [IBadgeClass(x) for x in get_all_badges()]
        result[ITEM_COUNT] = result[TOTAL] = len(items)
        return result
