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

import re
import SRS
from Shortcut import Shortcut

class Guarded(Shortcut):
  """This is the default subclass of SRS. An instance of this subclass
is actually constructed when "new SRS" is called.

Note that allowing variable separators after the SRS\d token means that
we must preserve this separator in the address for a possible reversal.
SRS1 does not need to understand the SRS0 address, just preserve it,
on the assumption that it is valid and that the host doing the final
reversal will perform cryptographic tests. It may therefore strip just
the string SRS0 and not the separator. This explains the appearance
of a double separator in SRS1<sep><hostname>=<sep>.

See Mail::SRS for details of the standard SRS subclass interface.
This module provides the methods compile() and parse(). It operates
without store, and guards against gaming the shortcut system."""
  def __init__(self,*args,**kw):
    self.srs0rek = re.compile(r'^%s(?=[-+=])' % SRS.SRS0TAG,re.IGNORECASE)
    Shortcut.__init__(self,*args,**kw)

  def compile(self,sendhost,senduser,srshost=None):

    senduser,m = self.srs1re.subn('',senduser,1)
    if m:
      # We could do a sanity check. After all, it might NOT be
      # an SRS address, unlikely though that is. We are in the
      # presence of malicious agents. However, since we don't need
      # to interpret it, it doesn't matter if it isn't an SRS
      # address. Our malicious SRS0 party gets back the garbage
      # he spat out.

      # Actually, it turns out that we can simplify this
      # function considerably, although it should be borne in mind
      # that this address is not opaque to us, even though we didn't
      # actually process or generate it.

      # hash, srshost, srsuser
      undef,srshost,srsuser = senduser.split(SRS.SRSSEP,2)

      hash = self.hash_create(srshost,srsuser)
      return SRS.SRS1TAG + self.separator + \
		SRS.SRSSEP.join((hash,srshost,srsuser))

    senduser,m = self.srs0rek.subn('',senduser,1)
    if m:
      hash = self.hash_create(sendhost, senduser)
      return SRS.SRS1TAG + self.separator + \
		SRS.SRSSEP.join((hash,sendhost,senduser))

    return Shortcut.compile(self,sendhost,senduser,srshost=srshost)

  def parse(self,user,srshost=None):
    user,m = self.srs1re.subn('',user,1)
    if m:
      hash,srshost,srsuser = user.split(SRS.SRSSEP, 2)[-3:]
      if hash.find('.') >= 0:
        assert self.allowunsafesrs, \
	  "Hashless SRS1 address received when AllowUnsafeSrs is not set"
	# Reconstruct the parameters as they were in the old format.
	srsuser = srshost + SRS.SRSSEP + srsuser
	srshost = hash
      else:
	assert srshost and srsuser, "Invalid SRS1 address"
	assert self.hash_verify(hash,srshost,srsuser), "Invalid hash"
      return srshost, SRS.SRS0TAG + srsuser

    return Shortcut.parse(self,user,srshost=srshost)
