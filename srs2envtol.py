#!/usr/bin/python2.3
# sendmail program map for SRS
#
# Use only if absolutely necessary.  It is *very* inefficient and
# a security risk.
#
# Copyright (c) 2004-2010 Business Management Systems. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the same terms as Python itself.

import SRS
import re
try:
  from configparser import ConfigParser, DuplicateSectionError
except:
  from ConfigParser import ConfigParser, DuplicateSectionError

# get SRS parameters from milter configuration
cp = ConfigParser({
  'secret': 'shhhh!',
  'maxage': '8',
  'hashlength': '8',
  'separator': '='
})
cp.read(["/etc/mail/pysrs.cfg"])
try:
  cp.add_section('srs')
except DuplicateSectionError:
  pass
srs = SRS.new(
  secret=cp.get('srs','secret'),
  maxage=cp.getint('srs','maxage'),
  hashlength=cp.getint('srs','hashlength'),
  separator=cp.get('srs','separator')
)
srs.warn = lambda x: x	# ignore case smash warning
del cp

def reverse(old_address):

  # Munge ParseLocal recipient in the same manner as required
  # in EnvFromSMTP.

  use_address = re.compile(r'[<>]').sub('',old_address)
  use_address = re.compile(r'\.$').sub('',use_address)

  # Just try and reverse the address. If we succeed, return this
  # new address; else, return the old address (quoted if it was
  # a piped alias).

  try:
    use_address = srs.reverse(use_address)
    while True:
      try:
        use_address = srs.reverse(use_address)
      except: break
    return use_address.replace('@','<@',1)+'.>'
  except:
    if use_address.startswith('|'):
      return '"%s"' % old_address
    else:
      return old_address

if __name__ == "__main__":
  import sys
  # No funny business in our output, please
  sys.stderr.close()
  print(reverse(sys.argv[1]))
