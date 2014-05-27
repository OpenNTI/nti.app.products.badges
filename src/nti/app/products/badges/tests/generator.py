#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import os
import random
import argparse

from sqlalchemy import create_engine

from tahrir_api.dbapi import TahrirDatabase
from tahrir_api.model import DeclarativeBase as tahrir_base

def generate_db(data_file, issuers=1, badges=1, persons=1):
	if os.path.exists(data_file):
		os.remove(data_file)

	dburi = "sqlite:///%s" % data_file
	manager = TahrirDatabase(dburi=dburi)
	metadata = getattr(tahrir_base, 'metadata')
	engine = create_engine(dburi)
	metadata.create_all(engine, checkfirst=True)

	issuers_ids = []
	for code in xrange(issuers):
		code += 1
		issuer_id = manager.add_issuer(origin=u'http://nti.com',
									   name=u'issuer.%s@Rnti' % code,
									   org=u'http://nti.com',
									   contact=u'issuer.%s@nti.com' % code)
		issuers_ids.append(issuer_id)

	for code in xrange(badges):
		code += 1
		tags = ''
		for x in xrange(random.randint(1, 3)):
			tags += 'tag.%s,' % (x + 1)
		manager.add_badge(name=u'badge.%s' % code,
						  image=u'http://nti.com/files/badge_%s.png' % code,
						  desc=u'Welcome to the Badge %s' % code,
						  criteria=u'http://nti.com/criteria/%s.html' % code,
						  issuer_id=random.choice(issuers_ids),
						  tags=tags)

	for code in xrange(persons):
		code += 1
		manager.add_person(email=u'person.%s@nti.com' % code,
						   nickname='person.%s' % code,
						   website='http://nti.com/persons/%s.htm' % code,
						   bio=u'I am person %s' % code)

def main(args=None):
	arg_parser = argparse.ArgumentParser(description="Create a sample tahrir db")
	arg_parser.add_argument('-f, ' '--file', help="Data file", dest='file',
							 default='sample.db')
	arg_parser.add_argument('-i', '--issuers',
							 dest='issuers',
							 default=1,
							 type=int,
							 help="The number of issuers")
	arg_parser.add_argument('-p', '--persons',
							 dest='persons',
							 default=1,
							 type=int,
							 help="The number of persons")
	arg_parser.add_argument('-b', '--badges',
							 dest='badges',
							 default=1,
							 type=int,
							 help="The number of persons")

	args = arg_parser.parse_args(args=args)

	generate_db(args.file, args.issuers, args.badges, args.persons)

if __name__ == '__main__':
	main()
