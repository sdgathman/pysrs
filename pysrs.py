#!/usr/bin/python2
# Sendmail socket server daemon
#
# Copyright (c) 2004-2010 Business Management Systems. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the same terms as Python itself.
from __future__ import print_function
import SRS
import SES
import re
import os
try:
  from configparser import ConfigParser, DuplicateSectionError
except:
  from ConfigParser import ConfigParser, DuplicateSectionError
import SocketMap
import time
import sys

class SRSHandler(SocketMap.Handler):

  def log(self,*msg):
    # print "%s [%d]" % (time.strftime('%Y%b%d %H:%M:%S'),self.id),
    print("%s" % (time.strftime('%Y%b%d %H:%M:%S'),), end=' ')
    for i in msg: print(i, end=' ')
    print()
    sys.stdout.flush()

  bracketRE = re.compile(r'[<>]')
  traildotRE = re.compile(r'\.$')

  # Our original envelope-from may look funny on entry
  # of this Ruleset:
  #
  #     admin<@asarian-host.net.>
  #
  # We need to preprocess it some:
  def _handle_make_srs(self,old_address):
    a = old_address.split('\x9b')
    if len(a) == 2:
      h,old_address = a
      self.log('h =',h)
    else:
      h = True
    nosrsdomain = self.server.nosrsdomain
    if old_address == '<@>' or not h or h in nosrsdomain:
      return old_address
    srs = self.server.srs
    ses = self.server.ses
    fwdomain = self.server.fwdomain
    if not fwdomain:
      fwdomain = self.fwdomain
    sesdomain = self.server.sesdomain
    signdomain = self.server.signdomain
    use_address = self.bracketRE.sub('',old_address)
    use_address = self.traildotRE.sub('',use_address)

    # Ok, first check whether we already have a signed SRS address;
    # if so, just return the old address: we do not want to double-sign
    # by accident!
    #
    # Else, gimme a valid SRS signed address, munge it back the way
    # sendmail wants it at this point; or just return the old address,
    # in case nothing went.

    try:
      new_address = srs.reverse(use_address)
      return old_address
    except:
      try:
        senduser,sendhost = use_address.split('@')
        shl = sendhost.lower()
        if shl in sesdomain:
          new_address = ses.sign(use_address)
        elif shl in signdomain:
          new_address = srs.sign(use_address)
        else:
          new_address = srs.forward(use_address,fwdomain)
        return new_address.replace('@','<@',1)+'.>'
      except:
        return old_address

  def _handle_reverse_srs(self,old_address):

    # Munge ParseLocal recipient in the same manner as required
    # in EnvFromSMTP.

    use_address = self.bracketRE.sub('',old_address)
    use_address = self.traildotRE.sub('',use_address)

    # Just try and reverse the address. If we succeed, return this
    # new address; else, return the old address (quoted if it was
    # a piped alias).

    srs = self.server.srs
    ses = self.server.ses
    try:
      a = ses.verify(use_address)
      if len(a) > 1:
        return a[0].replace('@','<@',1)+'.>'
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

def main(args):
# get SRS parameters from milter configuration
  cp = ConfigParser({
    'secret': 'shhhh!',
    'maxage': '8',
    'hashlength': '8',
    'separator': '=',
    'socket': '/var/run/milter/pysrs'
  })
  cp.read(["/etc/mail/pysrs.cfg"])
  try:
    cp.add_section('srs')
  except DuplicateSectionError:
    pass
  secret = [cp.get('srs','secret')]
  for old in ('secret.0','secret.1', 'secret.2'):
    if not cp.has_option('srs',old): break
    secret.append(cp.get('srs',old))
  srs = SRS.new(secret,
    maxage=cp.getint('srs','maxage'),
    hashlength=cp.getint('srs','hashlength'),
    separator=cp.get('srs','separator'),
    alwaysrewrite=True	# pysrs.m4 can skip calling us for local domains
  )
  ses = SES.new(secret, expiration=cp.getint('srs','maxage'))
  socket = cp.get('srs','socket')
  try:
    os.remove(socket)
  except: pass
  daemon = SocketMap.Daemon(socket,SRSHandler)
  daemon.server.fwdomain = cp.get('srs','fwdomain',None)
  daemon.server.sesdomain = ()
  daemon.server.signdomain = ()
  daemon.server.nosrsdomain = ()
  if cp.has_option('srs','ses'):
    daemon.server.sesdomain = [
            q.strip() for q in cp.get('srs','ses').split(',')]
  if cp.has_option('srs','sign'):
    daemon.server.signdomain = [
            q.strip() for q in cp.get('srs','sign').split(',')]
  if cp.has_option('srs','nosrs'):
    daemon.server.nosrsdomain = [
            q.strip() for q in cp.get('srs','nosrs').split(',')]
    
  daemon.server.srs = srs
  daemon.server.ses = ses
  print("%s pysrs startup" % time.strftime('%Y%b%d %H:%M:%S'))
  sys.stdout.flush()
  daemon.run()
  print("%s pysrs shutdown" % time.strftime('%Y%b%d %H:%M:%S'))

if __name__ == "__main__":
  main(sys.argv[1:])
