# $Log$
# Revision 1.4  2004/08/26 03:31:38  stuart
# Introduce sendmail socket map
#
# Revision 1.3  2004/03/25 00:02:21  stuart
# FIXME where case smash test depends on day
#
# Revision 1.2  2004/03/22 18:20:00  stuart
# Read config for sendmail maps from /etc/mail/pysrs.cfg
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

import unittest
from SRS.Guarded import Guarded
from SRS.DB import DB
from SRS.Reversible import Reversible
from SRS.Daemon import Daemon
import SRS
import threading
import socket

class SRSTestCase(unittest.TestCase):
  
  def setUp(self):
    # make sure user modified tag works
    SRS.SRS0TAG = 'ALT0'
    SRS.SRS1TAG = 'ALT1'

  def warn(self,*msg):
    self.case_smashed = True

  # There and back again
  def testGuarded(self):
    srs = Guarded()
    self.assertRaises(AssertionError,srs.forward,
    	'mouse@disney.com','mydomain.com')
    srs.set_secret('shhhh!')
    srs.separator = '+'
    sender = 'mouse@orig.com'
    srsaddr = srs.forward(sender,sender)
    self.assertEqual(srsaddr,sender)
    srsaddr = srs.forward(sender,'second.com')
    #print srsaddr
    self.failUnless(srsaddr.startswith(SRS.SRS0TAG))
    srsaddr1 = srs.forward(srsaddr,'third.com')
    #print srsaddr1
    self.failUnless(srsaddr1.startswith(SRS.SRS1TAG))
    srsaddr2 = srs.forward(srsaddr1,'fourth.com')
    #print srsaddr2
    self.failUnless(srsaddr2.startswith(SRS.SRS1TAG))
    addr = srs.reverse(srsaddr2)
    self.assertEqual(srsaddr,addr)
    addr = srs.reverse(srsaddr1)
    self.assertEqual(srsaddr,addr)
    addr = srs.reverse(srsaddr)
    self.assertEqual(sender,addr)

  def testCaseSmash(self):
    srs = SRS.new(secret='shhhhh!',separator='+')
    # FIXME: whether case smashing occurs depends on what day it is.
    sender = 'mouse@fickle1.com'
    srsaddr = srs.forward(sender,'second.com')
    self.failUnless(srsaddr.startswith(SRS.SRS0TAG))
    self.case_smashed = False
    srs.warn = self.warn
    addr = srs.reverse(srsaddr.lower())
    self.failUnless(self.case_smashed)	# check that warn was called
    self.assertEqual(sender,addr)

  def testReversible(self):
    srs = Reversible()
    self.assertRaises(AssertionError,srs.forward,
    	'mouse@disney.com','mydomain.com')
    srs.set_secret('shhhh!')
    srs.separator = '+'
    sender = 'mouse@orig.com'
    srsaddr = srs.forward(sender,sender)
    self.assertEqual(srsaddr,sender)
    srsaddr = srs.forward(sender,'second.com')
    #print srsaddr
    self.failUnless(srsaddr.startswith(SRS.SRS0TAG))
    srsaddr1 = srs.forward(srsaddr,'third.com')
    #print srsaddr1
    self.failUnless(srsaddr1.startswith(SRS.SRS0TAG))
    srsaddr2 = srs.forward(srsaddr1,'fourth.com')
    #print srsaddr2
    self.failUnless(srsaddr2.startswith(SRS.SRS0TAG))
    addr = srs.reverse(srsaddr2)
    self.assertEqual(srsaddr1,addr)
    addr = srs.reverse(srsaddr1)
    self.assertEqual(srsaddr,addr)
    addr = srs.reverse(srsaddr)
    self.assertEqual(sender,addr)

  def testDB(self,database='/tmp/srstest'):
    srs = DB(database=database)
    self.assertRaises(AssertionError,srs.forward,
    	'mouse@disney.com','mydomain.com')
    srs.set_secret('shhhh!')
    sender = 'mouse@orig.com'
    srsaddr = srs.forward(sender,sender)
    self.assertEqual(srsaddr,sender)
    srsaddr = srs.forward(sender,'second.com')
    #print srsaddr
    self.failUnless(srsaddr.startswith(SRS.SRS0TAG))
    srsaddr1 = srs.forward(srsaddr,'third.com')
    #print srsaddr1
    self.failUnless(srsaddr1.startswith(SRS.SRS0TAG))
    srsaddr2 = srs.forward(srsaddr1,'fourth.com')
    #print srsaddr2
    self.failUnless(srsaddr2.startswith(SRS.SRS0TAG))
    addr = srs.reverse(srsaddr2)
    self.assertEqual(srsaddr1,addr)
    addr = srs.reverse(srsaddr1)
    self.assertEqual(srsaddr,addr)
    addr = srs.reverse(srsaddr)
    self.assertEqual(sender,addr)

  def run2(self): # handle two requests
    self.daemon.server.handle_request()
    self.daemon.server.handle_request()

  def sendcmd(self,*args):
    sock = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    sock.connect(self.sockname)
    sock.send(' '.join(args)+'\n')
    res = sock.recv(128).strip()
    sock.close()
    return res

  def testExim(self,sockname='/tmp/srsd',secret="shhhh!"):
    self.sockname = sockname
    self.daemon = Daemon(socket=sockname,secret=secret)
    server = threading.Thread(target=self.run2,name='srsd')
    server.start()
    sender = 'mouse@orig.com'
    srsaddr = self.sendcmd('FORWARD',sender,'second.com')
    addr = self.sendcmd('REVERSE',srsaddr)
    server.join()
    self.assertEqual(sender,addr)

  def testProgMap(self):
    import envfrom2srs
    import srs2envtol
    orig = 'mickey<@orig.com.>'
    newaddr = envfrom2srs.forward(orig)
    self.failUnless(newaddr.endswith('.>'))
    addr2 = srs2envtol.reverse(newaddr)
    self.assertEqual(addr2,orig)
    # check case smashing by braindead mailers
    self.case_smashed = False
    srs2envtol.srs.warn = self.warn
    addr2 = srs2envtol.reverse(newaddr.lower())
    self.assertEqual(addr2,orig)
    self.failUnless(self.case_smashed)

def suite(): return unittest.makeSuite(SRSTestCase,'test')

if __name__ == '__main__':
    unittest.main()
