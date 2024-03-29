#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from io import BytesIO

from pyramid import httpexceptions as hexc

from pyramid.interfaces import IRequest

from pyramid.response import Response as PyramidResponse

from pyramid.threadlocal import get_current_request

from pyramid.view import view_config
from pyramid.view import view_defaults

import requests
from requests.structures import CaseInsensitiveDict

from six.moves import urllib_parse

from zope import component
from zope import interface

from zope.container.contained import Contained

from zope.event import notify

from zope.traversing.interfaces import IPathAdapter

from nti.app.base.abstract_views import AbstractView
from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.error import raise_json_error

from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.products.badges import MessageFactory as _

from nti.app.products.badges import OPEN_BADGES_VIEW
from nti.app.products.badges import OPEN_ISSUERS_VIEW
from nti.app.products.badges import OPEN_ASSERTIONS_VIEW

from nti.app.products.badges import is_locked
from nti.app.products.badges import get_badge
from nti.app.products.badges import add_person
from nti.app.products.badges import get_issuer
from nti.app.products.badges import add_assertion
from nti.app.products.badges import get_assertion
from nti.app.products.badges import person_exists
from nti.app.products.badges import get_user_email
from nti.app.products.badges import update_assertion
from nti.app.products.badges import is_email_verified

from nti.app.products.badges.interfaces import ACT_AWARD_BADGE
from nti.app.products.badges.interfaces import IBadgesWorkspace

from nti.app.products.badges.utils import get_badge_image_url

from nti.app.renderers.interfaces import INoHrefInResponse

from nti.appserver.workspaces.interfaces import IUserService

from nti.badges.interfaces import IEarnedBadge
from nti.badges.interfaces import IBadgeManager

from nti.badges.openbadges.interfaces import IBadgeClass
from nti.badges.openbadges.interfaces import IBadgeAssertion
from nti.badges.openbadges.interfaces import IIssuerOrganization

from nti.badges.openbadges.interfaces import BadgeAwardedEvent

from nti.badges.openbadges.utils.badgebakery import bake_badge

from nti.dataserver import authorization as nauth

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import IDataserverFolder

from nti.dataserver.users.users import User

from nti.externalization.externalization import to_external_object

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IPathAdapter)
@component.adapter(IUser, IRequest)
def BadgesWorkspacePathAdapter(context, unused_request):
    service = IUserService(context)
    workspace = IBadgesWorkspace(service)
    return workspace


@interface.implementer(IPathAdapter)
class BadgeAdminPathAdapter(Contained):

    __name__ = 'BadgeAdmin'

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.__parent__ = context


def _to_mozilla_backpack(context):
    result = to_external_object(context,
                                name="mozillabackpack",
                                decorate=False)
    return result


class OpenJSONView(AbstractView):

    def _set_environ(self):
        environ = self.request.environ
        environ['HTTP_X_REQUESTED_WITH'] = 'xmlhttprequest'


class Response(PyramidResponse):
    default_charset = None


# Issuers


@interface.implementer(IPathAdapter)
@component.adapter(IDataserverFolder, IRequest)
class OpenIssuersPathAdapter(Contained):

    def __init__(self, dataserver, unused_request):
        self.__parent__ = dataserver
        self.__name__ = OPEN_ISSUERS_VIEW

    def __getitem__(self, issuer_id):
        if not issuer_id:
            raise hexc.HTTPNotFound()
        issuer_id = urllib_parse.unquote(issuer_id)
        result = get_issuer(issuer_id)
        if result is not None:
            result = IIssuerOrganization(result)
            return result
        raise KeyError(issuer_id)


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             request_method='GET',
             context=IIssuerOrganization)
class OpenIssuerView(AbstractView):

    def __call__(self):
        result = self.request.context
        return result


@view_config(name="mozillabackpack")
@view_config(name="issuer.json")
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               request_method='GET',
               context=IIssuerOrganization)
class OpenIssuerJSONView(OpenJSONView):

    def __call__(self):
        self._set_environ()
        result = _to_mozilla_backpack(self.request.context)
        interface.alsoProvides(result, INoHrefInResponse)
        return result


# Badges


@interface.implementer(IPathAdapter)
@component.adapter(IDataserverFolder, IRequest)
class OpenBadgesPathAdapter(Contained):

    def __init__(self, dataserver, unused_request):
        self.__parent__ = dataserver
        self.__name__ = OPEN_BADGES_VIEW

    def __getitem__(self, badge_id):
        if not badge_id:
            raise hexc.HTTPNotFound()

        badge_id = urllib_parse.unquote(badge_id)
        result = get_badge(badge_id)
        if result is not None:
            result = IBadgeClass(result)
            return result
        raise KeyError(badge_id)


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             request_method='GET',
             context=IBadgeClass)
class OpenBadgeView(AbstractView):

    def __call__(self):
        result = self.request.context
        return result


@view_config(name="mozillabackpack")
@view_config(name="badge.json")
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               request_method='GET',
               context=IBadgeClass)
class OpenBadgeJSONView(OpenJSONView):

    def __call__(self):
        self._set_environ()
        result = _to_mozilla_backpack(self.request.context)
        interface.alsoProvides(result, INoHrefInResponse)
        return result


@view_config(name="award")
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               request_method='POST',
               context=IBadgeClass,
               permission=ACT_AWARD_BADGE)
class OpenBadgeAwardView(AbstractAuthenticatedView,
                         ModeledContentUploadRequestUtilsMixin):

    def readInput(self, value=None):
        result = super(OpenBadgeAwardView, self).readInput(value=value)
        return CaseInsensitiveDict(result)

    def __call__(self):
        values = self.readInput()
        username = values.get('user') \
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
        if not is_email_verified(user):
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(u"User email has not been verified."),
                                 'code': 'UserEmailUnverified',
                             },
                             None)
        # add person if required
        # an adapter must exists to convert the user to a person
        if not person_exists(user):
            add_person(user)

        # add assertion
        # pylint: disable=no-member
        name = self.context.name
        result = get_assertion(user, name)
        if result is None:
            add_assertion(user, name)
            result = get_assertion(user, name)
            notify(BadgeAwardedEvent(result, self.remoteUser))
            logger.info("Badge '%s' added to user %s",
                        name, username)
            result = IBadgeAssertion(result)
            return result

        raise_json_error(self.request,
                         hexc.HTTPUnprocessableEntity,
                         {
                             'message': _(u"Badge already awarded."),
                             'code': 'BadgeAlreadyAwarded',
                         },
                         None)


# Assertions


@interface.implementer(IPathAdapter)
@component.adapter(IDataserverFolder, IRequest)
class OpenAssertionsPathAdapter(Contained):

    def __init__(self, dataserver, unused_request):
        self.__parent__ = dataserver
        self.__name__ = OPEN_ASSERTIONS_VIEW

    def __getitem__(self, assertion_id):
        if not assertion_id:
            raise hexc.HTTPNotFound()
        assertion_id = urllib_parse.unquote(assertion_id)
        manager = component.getUtility(IBadgeManager)
        result = manager.get_assertion_by_id(assertion_id)
        if result is not None:
            result = IBadgeAssertion(result)
            return result
        raise KeyError(assertion_id)


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             request_method='GET',
             context=IBadgeAssertion)
class OpenAssertionView(AbstractView):

    def __call__(self):
        result = self.request.context
        return result


def get_badge_image_content(badge_url):
    # pylint: disable=unused-variable
    __traceback_info__ = badge_url
    res = requests.get(badge_url)
    if res.status_code != 200:
        logger.debug("Could not find image %s", badge_url)
        raise hexc.HTTPNotFound(_(u"Could not find badge image."))
    return res.content


def _get_badge_image_url(context, request=None):
    badge = IBadgeClass(context)
    badge_url = get_badge_image_url(badge, request)
    return badge_url


def _get_image(badge_url, payload=None, locked=False):
    content = get_badge_image_content(badge_url)
    target = source = BytesIO(content)
    source.seek(0)
    if locked:
        target = BytesIO()
        bake_badge(source, target,
                   payload=payload,
                   url=(badge_url if not payload else None))
        target.seek(0)
    return target


@view_config(name="baked-image")
@view_config(name="image.png")
@view_defaults(route_name='objects.generic.traversal',
               request_method='GET',
               context=IBadgeAssertion)
class OpenAssertionImageView(AbstractView):

    def __call__(self):
        context = self.request.context

        # baked image if locked
        locked = is_locked(context)
        badge_url = _get_badge_image_url(context, self.request)
        payload = _to_mozilla_backpack(context) if locked else None
        target = _get_image(badge_url, payload=payload, locked=locked)

        # return baked image
        response = Response()
        response.body_file = target
        response.content_type = 'image/png'
        response.content_disposition = 'attachment; filename="image.png"'
        return response


def assert_assertion_exported(context, remoteUser=None, request=None):
    context = context
    if is_locked(context):
        return

    # verify user access
    user = IUser(context, None)
    if user is None:
        request = request or get_current_request()
        raise_json_error(request,
                         hexc.HTTPUnprocessableEntity,
                         {
                             'message': _(u"Cannot find user for assertion."),
                             'code': 'AssertionNotFound',
                         },
                         None)
    if remoteUser is not None and remoteUser != user:
        raise hexc.HTTPForbidden()

    # check if email has been verified
    email = get_user_email(user)
    email_verified = is_email_verified(user)
    if not email or not email_verified:
        request = request or get_current_request()
        raise_json_error(request,
                         hexc.HTTPUnprocessableEntity,
                         {
                             'message': _(u"Cannot export assertion to an unverified email."),
                             'code': 'CannotExportAssertion',
                         },
                         None)
    update_assertion(context.uid, email=email, exported=True)


@view_config(name="mozillabackpack")
@view_config(name="assertion.json")
@view_defaults(route_name='objects.generic.traversal',
               request_method='GET',
               context=IBadgeAssertion)
class OpenAssertionJSONView(OpenJSONView):

    def __call__(self):
        context = self.request.context
        if not is_locked(context):
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(u"Assertion is not locked."),
                                 'code': 'AssertionIsNotLocked',
                             },
                             None)
        self._set_environ()
        external = _to_mozilla_backpack(context)
        interface.alsoProvides(external, INoHrefInResponse)
        return external


@view_config(name="lock")
@view_config(name="export")
@view_defaults(route_name='objects.generic.traversal',
               request_method='POST',
               context=IBadgeAssertion,
               permission=nauth.ACT_READ)
class ExportOpenAssertionView(AbstractAuthenticatedView):

    def __call__(self):
        context = self.request.context
        owner = IUser(context, None)
        if owner != self.remoteUser:
            raise hexc.HTTPForbidden()

        # verify the assertion can be exported
        assert_assertion_exported(context, self.remoteUser, self.request)
        payload = _to_mozilla_backpack(context)
        badge_url = _get_badge_image_url(context, self.request)
        target = _get_image(badge_url, payload=payload, locked=True)

        # return baked image
        response = Response()
        response.body_file = target
        response.content_type = 'image/png'
        response.content_disposition = 'attachment; filename="image.png"'
        return response


@view_config(name="lock")
@view_config(name="export")
@view_defaults(route_name='objects.generic.traversal',
               request_method='POST',
               context=IBadgeClass,
               permission=nauth.ACT_READ)
class LockBadgeView(AbstractAuthenticatedView):

    def __call__(self):
        context = self.request.context
        assertion = get_assertion(self.remoteUser, context.name)
        if assertion is None:
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(u"Cannot find user assertion."),
                                 'code': 'CannotFindAssertion',
                             },
                             None)

        # verify the assertion can be exported and export
        assert_assertion_exported(assertion, self.remoteUser)
        # Mark as earned badge (see decorators). We can do this because
        # badges are not persistent objects in ZODB
        interface.alsoProvides(context, IEarnedBadge)
        return context


@view_config(name="assertion")
@view_defaults(route_name='objects.generic.traversal',
               request_method='GET',
               context=IBadgeClass,
               permission=nauth.ACT_READ)
class BadgeAssertionView(AbstractAuthenticatedView):

    def __call__(self):
        context = self.request.context
        assertion = get_assertion(self.remoteUser, context.name)
        if assertion is None:
            raise_json_error(self.request,
                             hexc.HTTPNotFound,
                             {
                                 'message': _(u"Cannot find user assertion."),
                             },
                             None)
        return assertion
