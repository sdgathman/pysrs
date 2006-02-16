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
from Base import Base

class Shortcut(Base):

  """SRS.Shortcut - A shortcutting Sender Rewriting Scheme

SYNOPSIS

	import SRS.Shortcut
	srs = SRS.Shortcut(...)

DESCRIPTION

WARNING: Using the simple Shortcut strategy is a very bad idea. Use the
Guarded strategy instead. The weakness in the Shortcut strategy is
documented at http://www.anarres.org/projects/srs/

See Mail::SRS for details of the standard SRS subclass interface.
This module provides the methods compile() and parse(). It operates
without store, and shortcuts around all middleman resenders."""

  def compile(self,sendhost,senduser,srshost=None):

    senduser,m = self.srs0re.subn('',senduser,1)
    if m:
      # This duplicates effort in Guarded.pm but makes this file work
      # standalone.
      # We just do the split because this was hashed with someone
      # else's secret key and we can't check it.
      # hash, timestamp, host, user
      undef,undef,sendhost,senduser = senduser.split(SRS.SRSSEP,3)
      # We should do a sanity check. After all, it might NOT be
      # an SRS address, unlikely though that is. We are in the
      # presence of malicious agents. However, this code is
      # never reached if the Guarded subclass is used.
    else:
      senduser,m = self.srs1re.subn('',senduser,1)
      if m:
	# This should never be hit in practice. It would be bad.
	# Introduce compatibility with the guarded format?
	# SRSHOST, hash, timestamp, host, user
	sendhost,senduser = senduser.split(SRS.SRSSEP,5)[-2:]

    timestamp = self.timestamp_create()

    hash = self.hash_create(timestamp, sendhost, senduser)

    if sendhost == srshost:
      sendhost = ''
    # Note that there are 5 fields here and that sendhost may
    # not contain a valid separator. Therefore, we do not need to
    # escape separators anywhere in order to reverse this
    # transformation.
    return SRS.SRS0TAG + self.separator + \
    	SRS.SRSSEP.join((hash,timestamp,sendhost,senduser))

  def parse(self,user,srshost=None):
    user,m = self.srs0re.subn('',user,1)
    # We should deal with SRS1 addresses here, just in case?
    assert m, "Reverse address does not match %s." % self.srs0re.pattern

    # The 4 here matches the number of fields we encoded above. If
    # there are more separators, then they belong in senduser anyway.
    hash,timestamp,sendhost,senduser = user.split(SRS.SRSSEP,3)[-4:]
    if not sendhost and srshost:
      sendhost = srshost
    # Again, this must match as above.
    assert self.hash_verify(hash,timestamp,sendhost,senduser), "Invalid hash"

    assert self.timestamp_check(timestamp), "Invalid timestamp"
    return sendhost,senduser
