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

import bsddb
import time
import SRS
from Base import Base
from cPickle import dumps, loads

class DB(Base):
  """A MLDBM based Sender Rewriting Scheme

SYNOPSIS

	from SRS.DB import DB
	srs = DB(Database='/var/run/srs.db', ...)

DESCRIPTION

See Base.py for details of the standard SRS subclass interface.
This module provides the methods compile() and parse().

This module requires one extra parameter to the constructor, a filename
for a Berkeley DB_File database.

BUGS

This code relies on not getting collisions in the cryptographic
hash. This can and should be fixed.

The database is not garbage collected."""

  def __init__(self,database='/var/run/srs.db',hashlength=24,*args,**kw):
    Base.__init__(self,hashlength=hashlength,*args,**kw)
    assert database, "No database specified for SRS.DB"
    self.dbm = bsddb.btopen(database,'c')

  def compile(self,sendhost,senduser,srshost=None):
    ts = time.time()

    data = dumps((ts,sendhost,senduser))

    # We rely on not getting collisions in this hash.
    hash = self.hash_create(sendhost,senduser)

    self.dbm[hash] = data

    # Note that there are 4 fields here and that sendhost may
    # not contain a + sign. Therefore, we do not need to escape
    # + signs anywhere in order to reverse this transformation.
    return SRS.SRS0TAG + self.separator + hash

  def parse(self,user,srshost=None):
    user,m = self.srs0re.subn('',user,1)
    assert m, "Reverse address does not match %s." % self.srs0re.pattern

    hash = user
    data = self.dbm[hash]
    ts,sendhost,senduser = loads(data)

    assert self.hash_verify(hash,sendhost,senduser), "Invalid hash"

    assert self.time_check(ts), "Invalid timestamp"

    return (sendhost, senduser)
