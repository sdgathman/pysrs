#
# Class to sign and verify sender addresses with message ID.
#
# $Log$
# Revision 1.3  2011/03/03 23:52:21  customdesigned
# Release 1.0
#
# Revision 1.2  2010/03/17 22:05:34  customdesigned
# License updates.  Python code is Python license, except srsmilter.py.
# M4 sendmail macros are sendmail license.
#
# Revision 1.1  2005/06/18 21:44:40  customdesigned
# Changes since 0.30.9.  Begin SES support.
#
# Revision 1.8  2004/08/13 17:20:22  stuart
# Limit validations.
#
# Revision 1.7  2004/08/13 17:09:06  stuart
# support server id and fixed sigs
#
# Revision 1.6  2004/08/13 16:25:12  stuart
# bitpack function hopefully makes things clearer
#
# Revision 1.5  2004/08/04 21:58:11  stuart
# Tolerate case smashed tag.
#
# Revision 1.4  2004/08/04 15:43:25  stuart
# Drop Stuart's proposal.  Implement Seth's correctly, but with
# message id in high order bits.
#
# Revision 1.3  2004/08/03 13:05:20  stuart
# Base 38. 1/2 day timecode and fixed length hash for Seth.
#
# Revision 1.2  2004/08/02 18:50:04  stuart
# Implement Seth's format as well.
#
# Copyright (c) 2004-2010 Business Management Systems. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the same terms as Python itself.
#
import time
import hmac
try: from hashlib import sha1 as sha
except: import sha
import struct

DAY = 24*60*60	# size of day

# default encoding chars: base 38
BASE='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'

def longbits(hash,n):
  "Return leading n bits of hash digest converted to long."
  hashbits = 0
  h = 0
  for b in hash:
    h = (h << 8) + ord(b)
    hashbits += 8
    if hashbits >= n:
      return h >> (hashbits - n)
  return h

def bitpack(flds,*data):
  bits = 0
  for n,v in zip(flds,data):
    bits = (bits << n) | v
  return bits

def bitunpack(flds,bits):
  a = []
  f = list(flds[1:])
  f.reverse()
  for n in f:
    mask = (1 << n) - 1
    a.insert(0,bits & mask)
    bits >>= n
  a.insert(0,bits)
  return a

# Seth's proposal is to divide message ids into a fixed length fractional day
# plus a sequentially assigned id encoded variable length with leading
# zero supression.  This allows shorter ids for low volume sites without
# additional configuration.  The entire bitstring consisting of
# HMAC,ts,msgid is encoded as a block.
#
# If turns out to be much simpler to put the variable length msgid at
# the high order end, so I depart from Seth on that point, and encode
# the bitstring msgid,ts,HMAC as a block.  That way we don't have to
# worry about calculating the bit size of the encoded block based on
# the number of encoded chars.

class SES(object):

  def __init__(self,secret,hashbits=80,expiration=10,fbits=2,chars=BASE,
  	nservers=1,server=0,maxval=3):
    if type(secret) == str:
      self.secret = (secret,)
    else:
      self.secret = secret
    self.hashbits = hashbits
    self.chars = chars
    self.last_id = 0
    self.frac_day = DAY >> fbits
    self.last_ts = int(time.time() / self.frac_day)
    tsbits = 1
    while (1 << tsbits) - 1 <= expiration:
      tsbits += 1
    tsbits += fbits	  # bits needed for timecode
    self.expiration = expiration << fbits # expiration in frac days
    self.flds = (0,tsbits,hashbits)
    self.tcmask = (1 << tsbits) - 1
    self.nservers = nservers
    self.server = server
    self.valtrack = {}		# track validation attempts
    self.maxval = maxval	# maximum times a sig can be validated

  def timecode_as_secs(self,tc):
    "Return timecode converted to format compatible with time.time()."
    return tc * self.frac_day

  def get_timecode(self,s=None):
    "Return timecode from time.time() compatible value or current time."
    if s is None: s = time.time()
    return int(s / self.frac_day)

  def warn(self,*msg):
    print('WARNING:',' '.join(msg), file=sys.stderr)

  def set_secret(self,*args):
    """ses.set_secret(new,old,...)

Add a new secret to the rewriter. When an address is returned, all
secrets are tried to see if the hash can be validated. Don't use "foo",
"secret", "password", "10downing", "god" or "wednesday" as your secret."""
    self.secret = args

  def get_secret(self):
    "Return the list of secrets. These are secret. Don't publish them."
    return self.secret

  def create_message_id(self):
    "Assign timestamped message id.  Return timecode,msgid"
    # FIXME: synchronize for multithreading, make persistent
    ts = self.get_timecode()
    if ts == self.last_ts:	# if still same fractional day
      msgid = self.last_id + 1	#   assign next sequential id
    else:
      msgid = 1
    self.last_ts,self.last_id = ts,msgid
    return ts,msgid * self.nservers + self.server

  def encode(self,bits):
    "Convert sig bits to base n chars."
    chars = self.chars
    base = len(chars)
    t = []
    while bits > 0:
      bits,c = divmod(bits,base)
      t.append(chars[c])
    t.reverse()
    return ''.join(t)

  def decode(self,s):
    "Convert encoded chars to sig bits."
    chars = self.chars
    if chars == chars.upper():
      s = s.upper()
    base = len(chars)
    m = 0
    for c in s:
      m = m * base + chars.index(c)
    return m

  def hash_create(self,*data):
    """ses.hash_create(data,...)

Returns a cryptographic hash of all data in data as a long with
self.hashbits bits.  Any piece of data encoded into an address
which must remain inviolate should be hashed, so that when the
address is reversed, we can check that this data has not been
tampered with. You must provide at least one piece of data to
this method (otherwise this system is both cryptographically weak
and there may be collision problems with sender addresses)."""

    secret = self.get_secret()
    assert secret, "Cannot create a cryptographic MAC without a secret"
    h = hmac.new(secret[0],'',sha)
    for i in data:
      h.update(i)
    return longbits(h.digest(),self.hashbits)

  def hash_verify(self,hash,*data):
    """ses.hash_verify(hash,data,...)

Verify that data has not been tampered with, given the cryptographic
hash previously output by srs->hash_create(). Returns True or False.
All known secrets are tried in order to see if the hash was created
with an old secret."""

    secret = self.get_secret()
    assert secret, "Cannot verify a cryptographic MAC without a secret"
    hashes = []
    for s in secret:
      h = hmac.new(s,'',sha)
      for i in data:
	h.update(i)
      if hash == longbits(h.digest(),self.hashbits):
        return True
    return False;

  def sig_create(self,msgid,ts,h):
    """Return encoded signature.
    	msgid - long integer id unique for timecode
    	ts    - 32 bit timecode: day fractions since epoch
	h     - long with high order self.hashbits bits of hash digest"""
    if ts:
      return self.encode(bitpack(self.flds,msgid,ts % self.tcmask,h))
    else:
      return self.encode(bitpack(self.flds,msgid,self.tcmask,h))

  def sig_extract(self,sig,ts):
    """Return msgid,timecode,hash extracted from sig.
	sig - encoded sig returned by sig_create
	ts  - the current timecode
    """
    msgid,tc,hash = bitunpack(self.flds,self.decode(sig))
    tcmask = self.tcmask
    if tc != tcmask:
      tc = ts // tcmask * tcmask + int(tc)
      if tc > ts:
	tc -= tcmask
    else:
      tc = 0
    return msgid,tc,hash
   
  def sign(self,address,msgid=None):
    """Return signed address.
	if msgid is supplied, a fixed signature is generated."""
    local,domain = address.split('@',1)
    if msgid:	# fixed sig
      ts = 0
    else:
      ts,msgid = self.create_message_id()
    h = self.hash_create(struct.pack('>QQ',ts,msgid),local,'@',domain.lower())
    t = self.sig_create(msgid,ts,h)
    return 'SES=%s=%s@%s' % (t,local,domain)

  def verify(self,address):
    """Return unsigned_address,timecode,message_id.  Return (address,)
    unchanged if signature is invalid."""
    if address.upper().startswith('SES='):
      try:
	local,domain = address.split('@',1)
	tag,sig,user = local.split('=')
      except ValueError:
	raise ValueError("Invalid SES signature format: %s" % local)
      ts = self.get_timecode()
      msgid,tc,h = self.sig_extract(sig,ts)
      if not tc or ts - tc < self.expiration and self.hash_verify(h,
      	struct.pack('>QQ',tc,msgid),user,'@',domain.lower()):
	if tc:	# count validations
	  self.valtrack[msgid] = cnt = self.valtrack.get(msgid,0) + 1
	  if cnt > self.maxval:
	    raise RuntimeError(
	      "Too many validations of signature: %s" % address)
        return user + '@' + domain,tc,msgid
    return address,

if __name__ == '__main__':
  import sys
  ses = SES('shhhh!')
  for a in sys.argv[1:]:
    if a.startswith('-m'):
      ses.last_id = int(a[2:])
    elif a.startswith('SES'):
      print(ses.verify(a))
    else:
      print(ses.sign(a))
