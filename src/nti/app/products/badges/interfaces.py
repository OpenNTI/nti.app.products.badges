#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

from zope import interface

from nti.appserver import interfaces as app_interfaces

class IBadgesWorkspace(app_interfaces.IWorkspace):
    """
    A workspace containing data for badges.
    """

class IPrincipalBadgeManagerCatalog(interface.Interface):

    def iter_managers():
        """
        Iterate across :class:`nti.badges.interfaces.IBadgeManager` objects
        """
