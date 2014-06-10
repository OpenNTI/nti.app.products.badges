#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from pyramid.threadlocal import get_current_request

def has_side_effects(func):
    def wrapper(*args, **kwargs):
        request = get_current_request()
        if request is not None:
            request.environ[b'nti.request_had_transaction_side_effects'] = b'True'
        return func(*args, **kwargs)
    return wrapper
