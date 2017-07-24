# $Log$
# Revision 1.1.1.1  2005/06/03 04:13:18  customdesigned
# Initial import
#
# Revision 1.1.1.1  2004/03/19 05:23:13  stuart
# Import to CVS
#
#
# AUTHOR
# Shevek
# CPAN ID: SHEVEK
# cpan@anarres.org
# http://www.anarres.org/projects/
#
# Translated to Python by stuart@bmsi.com
# http://bmsi.com/python/milter.html
#
# Portions Copyright (c) 2004 Shevek. All rights reserved.
# Portions Copyright (c) 2004 Business Management Systems. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the same terms as Python itself.

import SRS
from .Shortcut import Shortcut

class Reversible(Shortcut):

  """A fully reversible Sender Rewriting Scheme

See SRS for details of the standard SRS subclass interface.
This module provides the methods compile() and parse(). It operates
without store."""

  def compile(self,sendhost,senduser,srshost=None):
    timestamp = self.timestamp_create()
    # This has to be done in compile, because we might need access
    # to it for storing in a database.
    hash = self.hash_create(timestamp,sendhost,senduser)
    if sendhost == srshost:
      sendhost = ''
    # Note that there are 4 fields here and that sendhost may
    # not contain a + sign. Therefore, we do not need to escape
    # + signs anywhere in order to reverse this transformation.
    return SRS.SRS0TAG + self.separator + \
        SRS.SRSSEP.join((hash,timestamp,sendhost,senduser))
