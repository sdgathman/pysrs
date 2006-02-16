# $Log$
# Revision 1.1.1.2  2005/06/03 04:13:55  customdesigned
# Support sendmail socketmap
#
# Revision 1.3  2004/06/09 00:29:25  stuart
# Use hmac instead of straight sha
#
# Revision 1.2  2004/03/22 18:20:19  stuart
# Missing import
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

import time
import hmac
import sha
import base64
import re
import SRS
import sys

BASE26 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
BASE32 = BASE26 + '234567'
BASE64 = BASE26 + BASE26.lower() + '0123456789+/'

# We have two options. We can either encode an send date or an expiry
# date. If we encode a send date, we have the option of changing
# the expiry date later. If we encode an expiry date, we can send
# different expiry dates for different sources/targets, and we don't
# have to store them.

# Do NOT use BASE64 since the timestamp_check routine now explicit
# smashes case in the timestamp just in case there was a problem.

BASE = BASE32
# This checks for more than one bit set in the size.
# i.e. is the size a power of 2?
base = len(BASE)
if base & (base - 1):
  raise ValueError("Invalid base array of size %d" % base)
PRECISION = 60 * 60 * 24	# One day
TICKSLOTS = base * base	# Two chars

class Base(object):
  def __init__(self,secret=None,maxage=SRS.SRSMAXAGE,
  	hashlength=SRS.SRSHASHLENGTH,
	hashmin=None,separator='=',alwaysrewrite=False,ignoretimestamp=False,
	allowunsafesrs=False):
    if type(secret) == str:
      self.secret = (secret,)
    else:
      self.secret = secret
    self.maxage = maxage
    self.hashlength =hashlength
    if hashmin: self.hashmin = hashmin
    else: self.hashmin = hashlength
    self.separator = separator
    if not separator in ('-','+','='):
      raise ValueError('separator must be = - or +, not %s' % separator)
    self.alwaysrewrite = alwaysrewrite
    self.ignoretimestamp = ignoretimestamp
    self.allowunsafesrs = allowunsafesrs
    self.srs0re = re.compile(r'^%s[-+=]' % SRS.SRS0TAG,re.IGNORECASE)
    self.srs1re = re.compile(r'^%s[-+=]' % SRS.SRS1TAG,re.IGNORECASE)
    #self.ses0re = re.compile(r'^%s[-+=]' % SRS.SES0TAG,re.IGNORECASE)

  def warn(self,*msg):
    print >>sys.stderr,'WARNING: ',' '.join(msg)

  def sign(self,sender):
    """srsaddress = srs.sign(sender)

Map a sender address into the same sender and a cryptographic cookie.
Returns an SRS address to use for preventing bounce abuse.

There are alternative subclasses, some of which will return SRS
compliant addresses, some will simply return non-SRS but valid RFC821
addresses. """
    try:
      senduser,sendhost = sender.split('@')
    except ValueError:
      raise ValueError("Sender '%s' must contain exactly one @" % sender)

    # Subclasses may override the compile() method.
    srsdata = self.compile(sendhost,senduser,srshost=sendhost)
    return '%s@%s' % (srsdata,sendhost)

  def forward(self,sender,alias,sign=False):
    """srsaddress = srs.forward(sender, alias)

Map a sender address into a new sender and a cryptographic cookie.
Returns an SRS address to use as the new sender.

There are alternative subclasses, some of which will return SRS
compliant addresses, some will simply return non-SRS but valid RFC821
addresses. """

    try:
      senduser,sendhost = sender.split('@')
    except ValueError:
      raise ValueError("Sender '%s' must contain exactly one @" % sender)

    # We don't require alias to be a full address, just a domain will do
    aliashost = alias.split('@')[-1]

    if aliashost.lower() == sendhost.lower() and not self.alwaysrewrite:
      return '%s@%s' % (senduser,sendhost)

    # Subclasses may override the compile() method.
    if sign:
      srsdata = self.compile(sendhost,senduser,srshost=aliashost)
    else:
      srsdata = self.compile(sendhost,senduser)
    return '%s@%s' % (srsdata,aliashost)

  def reverse(self,address):
    """sender = srs->reverse(srsaddress)

Reverse the mapping to get back the original address. Validates all
cryptographic and timestamp information. Returns the original sender
address. This method will die if the address cannot be reversed."""

    try:
      user,host = address.split('@')
    except ValueError:
      raise ValueError("Address '%s' must contain exactly one @" % address)

    sendhost,senduser = self.parse(user,srshost=host)
    return '%s@%s' % (senduser,sendhost)

  def compile(self,sendhost,senduser):
    """srsdata = srs.compile(host,user)

This method, designed to be overridden by subclasses, takes as
parameters the original host and user and must compile a new username
for the SRS transformed address. It is expected that this new username
will be joined on SRS.SRSSEP, and will contain a hash generated from
self.hash_create(...), and possibly a timestamp generated by
self.timestamp_create()."""
    raise NotImplementedError()

  def parse(self,srsuser):
    """host,user = srs.parse(srsuser)

This method, designed to be overridden by subclasses, takes an
SRS-transformed username as an argument, and must reverse the
transformation produced by compile(). It is required to verify any
hash and timestamp in the parsed data, using self.hash_verify(hash,
...) and self->timestamp_check(timestamp)."""
    raise NotImplementedError()

  def timestamp_create(self,ts=None):
    """timestamp = srs.timestamp_create(time)

Return a two character timestamp representing 'today', or time if
given. time is a Unix timestamp (seconds since the aeon).

This Python function has been designed to be agnostic as to base,
and in practice, base32 is used since it can be reversed even if a
remote MTA smashes case (in violation of RFC2821 section 2.4). The
agnosticism means that the Python uses division instead of rightshift,
but in Python that doesn't matter. C implementors should implement this
operation as a right shift by 5."""
    if not ts:
      ts = time.time()
    # Since we only mask in the bottom few bits anyway, we
    # don't need to take this modulo anything (e.g. @BASE^2).
    ts = int(ts // PRECISION)
    # print "Time is $time\n";
    mask = base - 1
    out = BASE[ts & mask]
    ts //= base	# Use right shift.
    return BASE[ts & mask]+out

  def timestamp_check(self,timestamp):
    """srs.timestamp_check(timestamp)

Return True if a timestamp is valid, False otherwise. There are 4096
possible timestamps, used in a cycle. At any time, $srs->{MaxAge}
timestamps in this cycle are valid, the last one being today. A
timestamp from the future is not valid, neither is a timestamp from
too far into the past. Of course if you go far enough into the future,
the cycle wraps around, and there are valid timestamps again, but the
likelihood of a random timestamp being valid is 4096/$srs->{MaxAge},
which is usually quite small: 1 in 132 by default."""
    if self.ignoretimestamp: return True
    ts = 0
    for d in timestamp.upper():	# LOOK OUT - USE BASE32
      ts = ts * base + BASE.find(d)
    now = (time.time() // PRECISION) % TICKSLOTS
    # print "Time is %d, Now is %d" % (ts,now)
    while now < ts: now += TICKSLOTS
    if now <= ts + self.maxage: return True
    return False

  def time_check(self,ts):
    """srs.time_check(time)

Similar to srs.timestamp_check(timestamp), but takes a Unix time, and
checks that an alias created at that Unix time is still valid. This is
designed for use by subclasses with storage backends."""
    return time.time() <= (ts + (self.maxage * PRECISION))

  def hash_create(self,*data):
    """srs.hash_create(data,...)

Returns a cryptographic hash of all data in data. Any piece of data
encoded into an address which must remain inviolate should be hashed,
so that when the address is reversed, we can check that this data has
not been tampered with. You must provide at least one piece of data
to this method (otherwise this system is both cryptographically weak
and there may be collision problems with sender addresses)."""

    secret = self.get_secret()
    assert secret, "Cannot create a cryptographic MAC without a secret"
    h = hmac.new(secret[0],'',sha)
    for i in data:
      h.update(i.lower())
    hash = base64.encodestring(h.digest())
    return hash[:self.hashlength]

  def hash_verify(self,hash,*data):
    """srs.hash_verify(hash,data,...)

Verify that data has not been tampered with, given the cryptographic
hash previously output by srs->hash_create(). Returns True or False.
All known secrets are tried in order to see if the hash was created
with an old secret."""

    if len(hash) < self.hashmin: return False
    secret = self.get_secret()
    assert secret, "Cannot create a cryptographic MAC without a secret"
    hashes = []
    for s in secret:
      h = hmac.new(s,'',sha)
      for i in data:
	h.update(i.lower())
      valid = base64.encodestring(h.digest())[:len(hash)]
      # We test all case sensitive matches before case insensitive
      # matches. While the risk of a case insensitive collision is
      # quite low, we might as well be careful.
      if valid == hash: return True
      hashes.append(valid)	# lowercase it later
    hash = hash.lower()
    for h in hashes:
      if hash == h.lower():
	self.warn("""SRS: Case insensitive hash match detected.
Someone smashed case in the local-part.""")
	return True
    return False;

  def set_secret(self,*args):
    """srs.set_secret(new,old,...)

Add a new secret to the rewriter. When an address is returned, all
secrets are tried to see if the hash can be validated. Don't use "foo",
"secret", "password", "10downing", "god" or "wednesday" as your secret."""
    self.secret = args

  def get_secret(self):
    "Return the list of secrets. These are secret. Don't publish them."
    return self.secret

  def separator(self):
    """srs.separator()

Return the initial separator, which follows the SRS tag. This is only
used as the initial separator, for the convenience of administrators
who wish to make srs0 and srs1 users on their mail servers and require
to use + or - as the user delimiter. All other separators in the SRS
address must be C<=>."""
    return self.separator
