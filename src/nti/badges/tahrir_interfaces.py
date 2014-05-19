#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

from zope import interface

from nti.utils import schema as nti_schema

from . import interfaces

class ITahrirModel(interface.Interface):
	pass

class IIssuer(ITahrirModel):
	id = nti_schema.Int(title=" Issuer id")
	origin = nti_schema.ValidTextLine(title=" Issuer origin")
	name = nti_schema.ValidTextLine(title=" Issuer name")
	org = nti_schema.ValidTextLine(title=" Issuer organization")
	contact = nti_schema.ValidTextLine(title=" Issuer contact")
	created_on =  nti_schema.ValidDatetime(title="Created time")

class IBadge(ITahrirModel):
	id = nti_schema.ValidTextLine(title=" Badge id")

	name = nti_schema.ValidTextLine(title=" Badge name")

	image = nti_schema.Variant((
					nti_schema.ValidTextLine(title="Image URL"),
					nti_schema.HTTPURL(title='Image URL')),
					title="Badge image")

	description = nti_schema.ValidText(title="Badge description")

	criteria = nti_schema.Variant((
					nti_schema.ValidTextLine(title="Criteria URL"),
					nti_schema.HTTPURL(title='Criteria URL')),
					title="Badge criteria")
	
	issuer_id = nti_schema.Int(title='Issuer id')

	created_on =  nti_schema.ValidDatetime(title="Created time")

	tags = nti_schema.ValidTextLine(title=" Badge tags")

class IPerson(ITahrirModel):
	id = nti_schema.Int(title="Person's id")

	email = nti_schema.ValidTextLine(title=" Person's email")

	nickname = nti_schema.ValidTextLine(title=" Person's nickname", required=False)

	website = nti_schema.Variant((
					nti_schema.ValidTextLine(title="Website URL"),
					nti_schema.HTTPURL(title='Website URL')),
					title="Person Website")

	bio = nti_schema.ValidText(title="Person's bio", required=False)

	created_on = nti_schema.ValidDatetime(title="Created time")

	last_login = nti_schema.ValidDatetime(title="Last login", required=False)
	opt_out = nti_schema.Bool(title="Opt out flag", required=False)
	rank = nti_schema.Int(title="Person's rank", required=False)

class IInvitation(ITahrirModel):
	id = nti_schema.ValidTextLine(title=" Invitation id")
	created_on = nti_schema.ValidDatetime(title="Created time")
	expires_on = nti_schema.ValidDatetime(title="Expiration time")
	badge_id = nti_schema.Int(title='Badge id')
	created_by = nti_schema.Int(title='Person id')

class IAuthorization(ITahrirModel):
	id = nti_schema.Int(title="Authorization's id")
	badge_id = nti_schema.ValidTextLine(title=" Badge id")
	person_id = nti_schema.Int(title="Person id")

class IAssertion(ITahrirModel):
	id = nti_schema.ValidTextLine(title="Assertion id")
	badge_id = nti_schema.ValidTextLine(title="Badge id")
	person_id = nti_schema.Int(title="Person's id")
	salt = nti_schema.ValidTextLine(title="Salt")
	issued_on = nti_schema.ValidDatetime(title="Issue date")
	issued_for = nti_schema.ValidTextLine(title="Issue for", required=False)
	recipient = nti_schema.ValidTextLine(title="Recipient ", required=False)

class ITahrirBadgeManager(interfaces.IBadgeManager):
	"""
	Interface for Tahrir database managers
	"""
