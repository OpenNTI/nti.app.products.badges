#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import is_not
from hamcrest import equal_to
from hamcrest import not_none
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property
does_not = is_not

import time
from datetime import datetime

from nti.externalization import internalization
from nti.externalization.externalization import toExternalObject

from nti.badges import interfaces
from nti.badges import openbadges

from nti.externalization.tests import externalizes

from nti.testing.matchers import verifiably_provides

from nti.badges.tests import NTIBadgesTestCase

class TestOpenBadges(NTIBadgesTestCase):

    def test_verification_object(self):
        vo = openbadges.VerificationObject(type="hosted", url="http://foo.json")
        assert_that(vo, verifiably_provides(interfaces.IVerificationObject))
        assert_that(vo, externalizes(has_entry('Class', 'VerificationObject')))

        ext_obj = toExternalObject(vo)
        factory = internalization.find_factory_for(ext_obj)
        assert_that(factory, is_(not_none()))

        new_vo = factory()
        internalization.update_from_external_object(new_vo, ext_obj)
        assert_that(new_vo, has_property('type', is_('hosted')))
        assert_that(new_vo, has_property('url', is_('http://foo.json')))
        
        assert_that(vo, equal_to(new_vo))

    def test_identity_object(self):
        io = openbadges.IdentityObject(identity="my-identity", type="email",
                                       hashed=True, salt="xyz")
        assert_that(io, verifiably_provides(interfaces.IIdentityObject))
        assert_that(io, externalizes(has_entry('Class', 'IdentityObject')))

        ext_obj = toExternalObject(io)
        factory = internalization.find_factory_for(ext_obj)
        assert_that(factory, is_(not_none()))

        new_io = factory()
        internalization.update_from_external_object(new_io, ext_obj)
        assert_that(new_io, has_property('identity', is_('my-identity')))
        assert_that(new_io, has_property('type', is_('email')))
        assert_that(new_io, has_property('hashed', is_(True)))
        assert_that(new_io, has_property('salt', is_('xyz')))

        assert_that(io, equal_to(new_io))

    def test_alignment_object(self):
        ao = openbadges.AlignmentObject(name="my-alignment", url=b"http://foo.xyz",
                                        description="foo")
        assert_that(ao, verifiably_provides(interfaces.IAlignmentObject))
        assert_that(ao, externalizes(has_entry('Class', 'AlignmentObject')))

        ext_obj = toExternalObject(ao)
        factory = internalization.find_factory_for(ext_obj)
        assert_that(factory, is_(not_none()))

        new_ao = factory()
        internalization.update_from_external_object(new_ao, ext_obj)
        assert_that(new_ao, has_property('name', is_('my-alignment')))
        assert_that(new_ao, has_property('url', is_(b'http://foo.xyz')))
        assert_that(new_ao, has_property('description', is_('foo')))
        
        assert_that(ao, equal_to(new_ao))

    def test_badge_class(self):
        
        ao1 = openbadges.AlignmentObject(name="my-alignment-1", url=b"http://foo-1.xyz",
                                        description="foo-1")
        
        ao2 = openbadges.AlignmentObject(name="my-alignment-2", url=b"http://foo-2.xyz",
                                        description="foo-2")

        bc = openbadges.BadgeClass(name="my-badge", description="super badge",
                                   image=b"https://badge.png",
                                   criteria=b"https://badge-criteria.com",
                                   issuer=b"https://badge-issuer.com",
                                   alignment=[ao1, ao2],
                                   )
        assert_that(bc, verifiably_provides(interfaces.IBadgeClass))
        assert_that(bc, externalizes(has_entry('Class', 'BadgeClass')))

        ext_obj = toExternalObject(bc)
        factory = internalization.find_factory_for(ext_obj)
        assert_that(factory, is_(not_none()))

        new_bc = factory()
        internalization.update_from_external_object(new_bc, ext_obj)
        assert_that(new_bc, has_property('name', is_('my-badge')))
        assert_that(new_bc, has_property('image', is_(b'https://badge.png')))
        assert_that(new_bc, has_property('criteria', is_(b'https://badge-criteria.com')))
        assert_that(new_bc, has_property('issuer', is_(b'https://badge-issuer.com')))
        assert_that(new_bc, has_property('description', is_('super badge')))
        assert_that(new_bc, has_property('alignment', has_length(2)))
        assert_that(new_bc, has_property('alignment', is_([ao1, ao2])))

        assert_that(bc, equal_to(new_bc))

    def test_badge_assertion(self):
        now = datetime.fromtimestamp(int(time.time()))
        verify = openbadges.VerificationObject(type="hosted", url="http://foo.json")
        recipient = openbadges.IdentityObject(identity="my-identity", type="email",
                                              hashed=True, salt="xyz")
        ba = openbadges.BadgeAssertion(uid="my-uid",
                                       recipient=recipient,
                                       verify=verify,
                                       badge=b"http://badge.json",
                                       issuedOn=now,
                                       image=b"http://foo.jpg",
                                       evidence=b"http://foo.com",
                                       expires=now)
        assert_that(ba, verifiably_provides(interfaces.IBadgeAssertion))
        assert_that(ba, externalizes(has_entry('Class', 'BadgeAssertion')))

        ext_obj = toExternalObject(ba)
        factory = internalization.find_factory_for(ext_obj)
        assert_that(factory, is_(not_none()))

        new_ba = factory()
        internalization.update_from_external_object(new_ba, ext_obj)
        assert_that(new_ba, has_property('uid', is_('my-uid')))
        assert_that(new_ba, has_property('verify', is_(equal_to(verify))))
        assert_that(new_ba, has_property('recipient', is_(equal_to(recipient))))
        assert_that(new_ba, has_property('issuedOn', is_(now)))
        assert_that(new_ba, has_property('image', is_(b'http://foo.jpg')))
        assert_that(new_ba, has_property('evidence', is_('http://foo.com')))
        assert_that(new_ba, has_property('expires', is_(now)))

        assert_that(ba, equal_to(new_ba))
