#!/usr/bin/python2.4
# Sendmail socket server daemon

import SRS
import SES
import re
import os
from ConfigParser import ConfigParser, DuplicateSectionError
import SocketMap
import time
import sys

class SRSHandler(SocketMap.Handler):

  def log(self,*msg):
    # print "%s [%d]" % (time.strftime('%Y%b%d %H:%M:%S'),self.id),
    print "%s" % (time.strftime('%Y%b%d %H:%M:%S'),),
    for i in msg: print i,
    print
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
    if old_address == '<@>':
      return old_address
    srs = self.server.srs
    ses = self.server.ses
    fwdomain = self.server.fwdomain
    if not fwdomain:
      fwdomain = self.fwdomain
    sesdomain = self.server.sesdomain
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
	if sendhost.lower() in sesdomain:
	  new_address = ses.sign(use_address)
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
  srs = SRS.new(
    secret=cp.get('srs','secret'),
    maxage=cp.getint('srs','maxage'),
    hashlength=cp.getint('srs','hashlength'),
    separator=cp.get('srs','separator'),
    alwaysrewrite=True	# pysrs.m4 can skip calling us for local domains
  )
  ses = SES.new(
    secret=cp.get('srs','secret'),
    expiration=cp.getint('srs','maxage')
  )
  socket = cp.get('srs','socket')
  try:
    os.remove(socket)
  except: pass
  daemon = SocketMap.Daemon(socket,SRSHandler)
  daemon.server.fwdomain = cp.get('srs','fwdomain',None)
  if cp.has_option('srs','ses'):
    daemon.server.sesdomain = [
    	q.strip() for q in cp.get('srs','ses').split(',')]
  else:
    daemon.server.sesdomain = []
  daemon.server.srs = srs
  daemon.server.ses = ses
  print "%s pysrs startup" % time.strftime('%Y%b%d %H:%M:%S')
  daemon.run()
  print "%s pysrs shutdown" % time.strftime('%Y%b%d %H:%M:%S')

if __name__ == "__main__":
  main(sys.argv[1:])
