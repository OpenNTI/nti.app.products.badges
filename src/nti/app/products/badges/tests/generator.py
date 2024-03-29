#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import os
import random
import argparse
from datetime import datetime

from sqlalchemy import create_engine

from tahrir_api.dbapi import TahrirDatabase
from tahrir_api.model import DeclarativeBase as tahrir_base


def generate_db(database, issuers=5, badges=5, persons=5, awards=0,
                verbose=False, person_prefix='person'):

    badge_ids = []
    person_ids = []
    issuer_ids = []
    for code in range(issuers):
        code += 1
        issuer_id = database.add_issuer(origin=u'http://nti.com',
                                        name=u'issuer_%s' % code,
                                        org=u'http://nti.com',
                                        contact=u'issuer.%s@nti.com' % code)
        issuer_ids.append(issuer_id)
        if verbose:
            print('Issuer %s added' % issuer_id)

    for code in range(badges):
        code += 1
        tags = ''
        for x in range(random.randint(1, 3)):
            tags += u'tag.%s,' % (x + 1)
        badge_id = database.add_badge(name=u'badge.%s' % code,
                                      desc=u'Badge %s' % code,
                                      image=u'badge_%s.png' % code,
                                      criteria=u'http://nti.com/criteria/%s.html' % code,
                                      issuer_id=random.choice(issuer_ids),
                                      tags=tags)
        badge_ids.append(badge_id)
        if verbose:
            print('Badge %s added' % badge_id)

    for code in range(persons):
        code += 1
        email = u'%s.%s@nti.com' % (person_prefix, code)
        person_id = database.add_person(email=email,
                                        nickname=email,
                                        website=u'http://nti.com/persons/%s.htm' % code,
                                        bio=u'I am person %s' % code)
        person_ids.append(person_id)
        if verbose:
            print('Person %s added', person_id)

    for code in range(awards):
        badge_id = random.choice(badge_ids)
        person_id = random.choice(person_ids)
        if not database.assertion_exists(badge_id, person_id):
            database.add_assertion(badge_id,
                                   person_id,
                                   datetime.now(),
                                   notify=False)
            if verbose:
                print('Badge %s awarded to %s' % (badge_id, person_id))

    return database


def generate(dburi, issuers=5, badges=5, persons=5, awards=0, verbose=False):
    database = TahrirDatabase(dburi=dburi)
    metadata = getattr(tahrir_base, 'metadata')
    engine = create_engine(dburi)
    metadata.create_all(engine, checkfirst=True)
    generate_db(database, issuers, badges, persons, awards, verbose)
    return database


def main(args=None):
    arg_parser = argparse.ArgumentParser(description="Create a sample tahrir db")
    arg_parser.add_argument('-f, ' '--file', help="Data file", dest='file',
                            default='tahrir.db')
    arg_parser.add_argument('-v', '--verbose', help="Be verbose", action='store_true',
                            dest='verbose')
    arg_parser.add_argument('-i', '--issuers',
                            dest='issuers',
                            default=5,
                            type=int,
                            help="The number of issuers")
    arg_parser.add_argument('-p', '--persons',
                            dest='persons',
                            default=5,
                            type=int,
                            help="The number of persons")
    arg_parser.add_argument('-b', '--badges',
                            dest='badges',
                            default=5,
                            type=int,
                            help="The number of persons")
    arg_parser.add_argument('-a', '--awards',
                            dest='awards',
                            default=0,
                            type=int,
                            help="The number of awards")

    args = arg_parser.parse_args(args=args)

    if os.path.exists(args.file):
        os.remove(args.file)

    dburi = "sqlite:///%s" % os.path.expanduser(args.file)
    generate(dburi, args.issuers, args.badges, args.persons, args.awards,
             verbose=args.verbose)


if __name__ == '__main__':
    main()
