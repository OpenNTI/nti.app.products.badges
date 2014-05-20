#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface
from zope.container import contained

import persistent

from nti.externalization.externalization import make_repr

from nti.utils.schema import SchemaConfigured
from nti.utils.schema import createDirectFieldProperties

from . import interfaces as badges_interfaces

@interface.implementer(badges_interfaces.IVerificationObject)
class VerificationObject(SchemaConfigured, persistent.Persistent, contained.Contained):
    createDirectFieldProperties(badges_interfaces.IVerificationObject)

    __external_can_create__ = True
    mime_type = mimeType = 'application/vnd.nextthought.badges.verificationobject'

    def __init__(self, *args, **kwargs):
        persistent.Persistent.__init__(self)
        SchemaConfigured.__init__(self, *args, **kwargs)

    def __eq__(self, other):
        try:
            return self is other or (self.type == other.type and self.url == other.url)
        except AttributeError:
            return NotImplemented

    __repr__ = make_repr()

    def __hash__(self):
        xhash = 47
        xhash ^= hash(self.url)
        xhash ^= hash(self.type)
        return xhash

@interface.implementer(badges_interfaces.IIdentityObject)
class IdentityObject(SchemaConfigured, persistent.Persistent, contained.Contained):
    createDirectFieldProperties(badges_interfaces.IIdentityObject)

    __external_can_create__ = True
    mime_type = mimeType = 'application/vnd.nextthought.badges.identityobject'

    def __init__(self, *args, **kwargs):
        persistent.Persistent.__init__(self)
        SchemaConfigured.__init__(self, *args, **kwargs)

    def __eq__(self, other):
        try:
            return self is other or (self.identity == other.identity
                                     and self.type == other.type)
        except AttributeError:
            return NotImplemented

    __repr__ = make_repr()

    def __hash__(self):
        xhash = 47
        xhash ^= hash(self.type)
        xhash ^= hash(self.identity)
        return xhash

@interface.implementer(badges_interfaces.IAlignmentObject)
class AlignmentObject(SchemaConfigured, persistent.Persistent, contained.Contained):
    createDirectFieldProperties(badges_interfaces.IAlignmentObject)

    __external_can_create__ = True
    mime_type = mimeType = 'application/vnd.nextthought.badges.alignmentobject'

    def __init__(self, *args, **kwargs):
        persistent.Persistent.__init__(self)
        SchemaConfigured.__init__(self, *args, **kwargs)

    def __eq__(self, other):
        try:
            return self is other or (self.name == other.name and self.url == other.url)
        except AttributeError:
            return NotImplemented

    __repr__ = make_repr()

    def __hash__(self):
        xhash = 47
        xhash ^= hash(self.url)
        xhash ^= hash(self.name)
        return xhash

@interface.implementer(badges_interfaces.IBadgeClass)
class BadgeClass(SchemaConfigured, persistent.Persistent, contained.Contained):
    createDirectFieldProperties(badges_interfaces.IBadgeClass)

    __external_can_create__ = True
    mime_type = mimeType = 'application/vnd.nextthought.badges.badgeclass'

    def __init__(self, *args, **kwargs):
        persistent.Persistent.__init__(self)
        SchemaConfigured.__init__(self, *args, **kwargs)

    def __eq__(self, other):
        try:
            return self is other or (self.name == other.name)
        except AttributeError:
            return NotImplemented

    __repr__ = make_repr()

    def __hash__(self):
        xhash = 47
        xhash ^= hash(self.name)
        return xhash

@interface.implementer(badges_interfaces.IBadgeAssertion)
class BadgeAssertion(SchemaConfigured, persistent.Persistent, contained.Contained):
    createDirectFieldProperties(badges_interfaces.IBadgeAssertion)

    __external_can_create__ = True
    mime_type = mimeType = 'application/vnd.nextthought.badges.badgeassertion'

    def __init__(self, *args, **kwargs):
        persistent.Persistent.__init__(self)
        SchemaConfigured.__init__(self, *args, **kwargs)

    def __eq__(self, other):
        try:
            return self is other or (self.uid == other.uid
                                     and self.recipient == other.recipient)
        except AttributeError:
            return NotImplemented

    __repr__ = make_repr()

    def __hash__(self):
        xhash = 47
        xhash ^= hash(self.uid)
        xhash ^= hash(self.recipient)
        return xhash
