# Exim compatible socket server for SRS
# $Log$
# Revision 1.3  2004/08/26 03:31:38  stuart
# Introduce sendmail socket map
#
# Revision 1.2  2004/03/23 18:46:38  stuart
# support commandline args for key
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

from .Guarded import Guarded
import os
import os.path
import socketserver

SRSSOCKET = '/tmp/srsd';

class EximHandler(socketserver.StreamRequestHandler):

  def handle(self):
    srs = self.server.srs
    sock = self.rfile
    try:
      line = self.rfile.readline()
      #print "Read '%s' on %s\n" % (line.strip(),self.request)
      args = line.split()
      cmd = args.pop(0).upper()
      if cmd == 'FORWARD':
        res = srs.forward(*args)
      elif cmd == 'REVERSE':
        res = srs.reverse(*args)
      else:
        raise ValueError("Invalid command %s" % cmd)
    except Exception as x:
      res = "ERROR: %s"%x
    self.wfile.write(res+'\n')


class Daemon(object):
  def __init__(self,secret=None,secretfile=None,socket=SRSSOCKET,
    *args,**kw):
    secrets = []
    if secret: secrets += secret
    if secretfile and os.path.exists(secretfile):
      assert os.path.isfile(secretfile) and os.access(secretfile,os.R_OK), \
        "Secret file $secretfile not readable"
      FH = open(secretfile)
      for ln in FH:
        if not ln: continue
        if ln.startswith('#'): continue
        secrets += ln
      FH.close()

    assert secrets, \
      """No secret or secretfile given. Use --secret or --secretfile,
and ensure the secret file is not empty."""

    # Preserve the pertinent original arguments, mostly for fun.
    self.secret = secret
    self.secretfile = secretfile
    self.socket = socket
    self.srs = Guarded(secret=secrets,*args,**kw)
    try:
      os.unlink(socket)
    except:
      pass
    self.server = socketserver.UnixStreamServer(socket,EximHandler)
    self.server.srs = self.srs

  def run(self):
    self.server.serve_forever()

def main(args):
  from getopt import getopt
  opts,args = getopt(args,'',['secret=','secretfile='])
  kw = dict([(opt[2:],val) for opt,val in opts])
  server = Daemon(*args,**kw)
  server.run()

if __name__ == '__main__':
  import sys
  main(sys.argv[1:])
