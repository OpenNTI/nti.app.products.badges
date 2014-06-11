#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import sys
import argparse

from zope.configuration import xmlconfig, config
from zope.dottedname import resolve as dottedname

from nti.badges.openbadges.utils import scanner, DEFAULT_SECRET

from nti.dataserver.utils import run_with_dataserver

from .. import add_badge
from .. import add_issuer
from .. import badge_exists
from .. import update_badge
from .. import issuer_exists

def sync_db(path, update=False, verify=False, **kwargs):
	badges = 0
	issuers = 0

	path = os.path.expanduser(path)
	logger.info("Scanning %s", path)
	results = scanner.flat_scan(path, verify=verify, **kwargs)  # pairs mozilla badge/issuer
	if not results:
		logger.warn("No badges found")
		return (issuers, badges)

	for badge, issuer in results:
		if issuer is None:
			logger.debug("Badge %s cannot be processed; issuer not found",
						 badge.name)
			continue

		if not issuer_exists(issuer):
			issuers += 1
			add_issuer(issuer)
			logger.debug("Issuer %s,%s added", issuer.name, issuer.url)

		if not badge_exists(badge):
			badges += 1
			add_badge(badge, issuer)
			logger.debug('Badge %s added', badge.name)
		elif update:
			badges += 1
			update_badge(badge)
			logger.debug('Badge %s updated', badge.name)

	return (issuers, badges)

def _create_context(env_dir):
	env_dir = os.path.expanduser(env_dir)

	# find the ds etc directory
	etc = os.getenv('DATASERVER_ETC_DIR') or os.path.join(env_dir, 'etc')
	etc = os.path.expanduser(etc)

	context = config.ConfigurationMachine()
	xmlconfig.registerCommonDirectives(context)

	slugs = os.path.join(etc, 'package-includes')
	if os.path.exists(slugs) and os.path.isdir(slugs):
		package = dottedname.resolve('nti.dataserver')
		context = xmlconfig.file('configure.zcml', package=package, context=context)
		xmlconfig.include(context, files=os.path.join(slugs, '*.zcml'),
						  package='nti.appserver')
	return context

def do_sync(path, update=False, verify=False, verbose=False, **kwargs):
	issuers, badges = sync_db(path, update, verify, **kwargs)
	if verbose:
		print('Issuers...', issuers)
		print('Badges....', badges)

def process_args(args=None):
	arg_parser = argparse.ArgumentParser(description="Sync badges")
	arg_parser.add_argument('-v', '--verbose', help="Verbose", action='store_true',
							 dest='verbose')
	arg_parser.add_argument('-d', '--dir',
							 dest='directory',
							 help="Hosted badge images directory")
	arg_parser.add_argument('-s', '--secret',
							 dest='secret',
							 default=DEFAULT_SECRET,
							 help="JSON web signature secret")
	arg_parser.add_argument('-u', '--update', help="Update", action='store_true',
							 dest='update')
	arg_parser.add_argument('-y', '--verify', help="Verify badge data", action='store_true',
							 dest='verify')

	args = arg_parser.parse_args(args=args)

	directory = args.directory
	if not directory:
		directory = os.getenv('HOSTED_BADGE_IMAGES_DIR')

	directory = os.path.expanduser(directory) if directory else directory
	if not directory or not os.path.exists(directory) or not os.path.isdir(directory):
		print("Invalid badge directory", directory, file=sys.stderr)
		sys.exit(2)

	env_dir = os.getenv('DATASERVER_DIR')
	context = _create_context(env_dir)
	conf_packages = ('nti.appserver',)
	run_with_dataserver(environment_dir=env_dir,
						xmlconfig_packages=conf_packages,
						verbose=args.verbose,
						context=context,
						minimal_ds=False,
						function=lambda: do_sync(directory, args.update, args.verify,
												 verbose=args.verbose,
												 secret=args.secret))
def main(args=None):
	process_args(args)
	sys.exit(0)

if __name__ == '__main__':
	main()
