#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

from zope import interface

from nti.appserver import interfaces as app_interfaces

from nti.badges.interfaces import IBadgeManager

from nti.utils import schema as nti_schema

class IBadgesWorkspace(app_interfaces.IWorkspace):
    """
    A workspace containing data for badges.
    """

class IPrincipalBadgeManager(interface.Interface):
    manager = nti_schema.Object(IBadgeManager, title="badge manager")

