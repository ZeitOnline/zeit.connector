# Copyright (c) 2007-2008 gocept gmbh & co. kg
# See also LICENSE.txt
# $Id$

import os
import unittest

from zope.testing import doctest


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocFileSuite(
        'profiling.txt',
        optionflags=(doctest.REPORT_NDIFF + doctest.NORMALIZE_WHITESPACE +
                     doctest.ELLIPSIS)))
    return suite
