#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

from zope import interface
from zope.schema import vocabulary

from nti.dataserver import interfaces as nti_interfaces

from nti.utils import schema as nti_schema

VO_TYPE_HOSTED = u'hosted'
VO_TYPE_SIGNED = u'signed'
VO_TYPES = (VO_TYPE_HOSTED, VO_TYPE_SIGNED)
VO_TYPES_VOCABULARY = \
	vocabulary.SimpleVocabulary([vocabulary.SimpleTerm(_x) for _x in VO_TYPES])

ID_TYPE_EMAIL = u'email'
ID_TYPES = (ID_TYPE_EMAIL,)
ID_TYPES_VOCABULARY = \
	vocabulary.SimpleVocabulary([vocabulary.SimpleTerm(_x) for _x in ID_TYPES])

class IVerificationObject(interface.Interface):
	type = nti_schema.Choice(vocabulary=VO_TYPES_VOCABULARY,
							title='Verification method',
							required=True)
	url = nti_schema.Variant((
					nti_schema.TextLine(title='URL assertion/issuer public key'),
					nti_schema.HTTPURL(title='URL assertion/issuer public key')),
					title="URL pointing to the assertion or issuer's public key")


class IIdentityObject(interface.Interface):
	identity = nti_schema.ValidTextLine(title="identity hash or text")

	type = nti_schema.Choice(vocabulary=ID_TYPES_VOCABULARY,
							 title='The type of identity',
							 required=True, default=ID_TYPE_EMAIL)

	hashed = nti_schema.Bool(title='Whether or not the id value is hashed',
							 required=False, default=False)

	salt = nti_schema.ValidTextLine(title="Salt string", required=False)

class IAlignmentObject(interface.Interface):
	name = nti_schema.ValidTextLine(title="The name of the alignment")
	url = nti_schema.HTTPURL(title='URL linking to the official description of the standard')
	description = nti_schema.ValidText(title="Short description of the standard",
                                       required=False)

class IBadgeClass(nti_interfaces.IUserTaggedContent):
	name = nti_schema.ValidTextLine(title="The name of the achievement")
	
	description = nti_schema.ValidText(title="A short description of the achievement")
	
	image = nti_schema.Variant((
					nti_schema.DataURI(title="Image data"),
					nti_schema.HTTPURL(title='Image URL')),
					title="Image representing the achievement")

	criteria = nti_schema.HTTPURL(title='URL of the criteria for earning the achievement')

	issuer = nti_schema.HTTPURL(title='URL of the organization that issued the badge')

	alignment = nti_schema.ListOrTuple(value_type=nti_schema.Object(IAlignmentObject),
                                       title="Objects describing which educational standards",
                                       required=False,
                                       min_length=0)

class IBadgeAssertion(interface.Interface):
	uid = nti_schema.ValidTextLine(title=" Unique Identifier for the badge")

	recipient = nti_schema.Object(IIdentityObject,
								  title="The recipient of the achievement")
	badge = nti_schema.Variant((
					nti_schema.Object(IBadgeClass, title="Badge class"),
					nti_schema.HTTPURL(title='badge URL')),
					title="badge being awarded")

	verify = nti_schema.Object(IVerificationObject,
							   title="Data to help a third party verify this assertion")

	issuedOn = nti_schema.ValidDatetime(title="date that the achievement was awarded")

	image = nti_schema.Variant((
					nti_schema.DataURI(title="Image data"),
					nti_schema.HTTPURL(title='Image URL')),
					title="Image representing this user's achievement",
					required=False)

	evidence = nti_schema.HTTPURL(
					title='URL of the work that the recipient did to earn the achievement',
					required=False)

	expires = nti_schema.ValidDatetime(title="Achievment expiry", required=False)


class IBadgeManager(interface.Interface):
	pass

