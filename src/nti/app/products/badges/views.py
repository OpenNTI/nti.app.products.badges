#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pyramid views.

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface
from zope.traversing.interfaces import IPathAdapter

from pyramid.interfaces import IRequest

from nti.appserver.interfaces import IUserService

from nti.dataserver import interfaces as nti_interfaces

from . import interfaces

@interface.implementer(IPathAdapter)
@component.adapter(nti_interfaces.IUser, IRequest)
def BadgesPathAdapter(context, request):
    service = IUserService(context)
    workspace = interfaces.IBadgesWorkspace(service)
    return workspace
