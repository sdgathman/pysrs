#
# Original AUTHOR: Shevek
# CPAN ID: SHEVEK
# cpan@anarres.org
# http://www.anarres.org/projects/
#
# Translated to Python by stuart@bmsi.com
# http://bmsi.com/python/milter.html
#
# Copyright (c) 2017,2020 Stuart Gathman  All rights reserved.
# Portions Copyright (c) 2004 Shevek. All rights reserved.
# Portions Copyright (c) 2004,2006 Business Management Systems. All rights
# reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the same terms as Python itself.

import unittest
import Milter
from Milter.test import TestBase
from SRS.Guarded import Guarded
from SRS.DB import DB
from SRS.Reversible import Reversible
from SRS.Daemon import Daemon
import srsmilter
import SRS,SES
import threading
import socket
try:
  from io import BytesIO
except:
  from StringIO import StringIO as BytesIO

class TestMilter(TestBase,srsmilter.srsMilter):
  def __init__(self):
    TestBase.__init__(self)
    srsmilter.config = srsmilter.Config(['pysrs.cfg'])
    srsmilter.srsMilter.__init__(self)
    self.setsymval('j','test.milter.org')

class SocketMap(object):
  def __init__(self,sockname):
    self.sockname = sockname
    self.sock = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    self.sock.connect(self.sockname)
    self.rfile = self.sock.makefile('rb')

  def _readlen(self,maxlen=8):
    ch = self.rfile.read(1)
    n = b''
    while ch != b':':
      if not ch:
        raise EOFError
      if not ch in b'0123456789':
        print('n =',n,'ch =',ch)
        raise ValueError
      if len(n) >= maxlen:
        raise OverflowError
      n += ch
      ch = self.rfile.read(1)
    return int(n)

  def sendmap(self,mapname,*args):
    # Sample req: 'make_srs unilit.us.\x9bstuart<@gathman.org.>'
    s = mapname.encode() + b' '+b'\x9b'.join(s.encode() for s in args)
    self.sock.send(b'%d:%s,' % (len(s),s))
    n = self._readlen()
    res = self.rfile.read(n)
    ch = self.rfile.read(1)
    if ch == b',':
      return res.decode().split(' ',1)
    if ch == b'':
      raise EOFError
    raise ValueError

  def close(self):
    self.rfile.close()
    self.sock.close()

class SRSMilterTestCase(unittest.TestCase):

  msg = b'''From: good@example.com
Subject: test

test
'''

  ## Test rejecting bounce spam
  def testReject(self):
    milter = TestMilter()
    milter.conf.srs_domain = set(['example.com'])
    milter.conf.srs_reject_spoofed = False
    fp = BytesIO(self.msg)
    rc = milter.connect('testReject',ip='192.0.3.1')
    self.assertEqual(rc,Milter.CONTINUE)
    rc = milter.feedFile(fp,sender='',rcpt='good@example.org')
    self.assertEqual(rc,Milter.CONTINUE)
    milter.conf.srs_reject_spoofed = True
    fp.seek(0)
    rc = milter.feedFile(fp,sender='',rcpt='bad@example.com')
    self.assertEqual(rc,Milter.REJECT)
    milter.close()

  ## Test SRS coding of MAIL FROM
  def testSign(self):
    milter = TestMilter()
    milter.conf.signdomain = set(['example.com'])
    milter.conf.miltersrs = True
    fp = BytesIO(self.msg)
    rc = milter.connect('testSign',ip='192.0.3.1')
    self.assertEqual(rc,Milter.CONTINUE)
    fp.seek(0)
    rc = milter.feedFile(fp,sender='good@example.com',rcpt='good@example.org')
    self.assertEqual(rc,Milter.CONTINUE)
    s = milter.conf.srs.reverse(milter._sender[1:-1])
    self.assertEqual(s,'good@example.com')
    # check that it doesn't happen when disabled
    milter.conf.miltersrs = False
    fp.seek(0)
    rc = milter.feedFile(fp,sender='good@example.com',rcpt='good@example.org')
    self.assertEqual(rc,Milter.CONTINUE)
    self.assertEqual(milter._sender,'<good@example.com>')
    milter.close()

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
    sender = '"Blah blah"@orig.com'
    srsaddr = srs.forward(sender,sender)
    self.assertEqual(srsaddr,sender)
    srsaddr = srs.forward(sender,'second.com')
    self.assertTrue(srsaddr.startswith('"'+SRS.SRS0TAG),srsaddr)
    srsaddr1 = srs.forward(srsaddr,'third.com')
    #print srsaddr1
    self.assertTrue(srsaddr1.startswith('"'+SRS.SRS1TAG))
    srsaddr2 = srs.forward(srsaddr1,'fourth.com')
    #print srsaddr2
    self.assertTrue(srsaddr2.startswith('"'+SRS.SRS1TAG))
    addr = srs.reverse(srsaddr2)
    self.assertEqual(srsaddr,addr)
    addr = srs.reverse(srsaddr1)
    self.assertEqual(srsaddr,addr)
    addr = srs.reverse(srsaddr)
    self.assertEqual(sender,addr)

  def testSign(self):
    srs = Guarded()
    srs.set_secret('shhhh!')
    srs.separator = '+'
    sender = 'mouse@orig.com'
    sig = srs.sign(sender)
    addr = srs.reverse(sig)
    self.assertEqual(sender,addr)
    sender = 'mouse@ORIG.com'
    sig = srs.sign(sender)
    addr = srs.reverse(sig)
    self.assertEqual(sender,addr)
    addr = srs.reverse(sig.lower())
    self.assertEqual(sender.lower(),addr)

  def testCaseSmash(self):
    srs = SRS.new(secret='shhhhh!',separator='+')
    # FIXME: whether case smashing occurs depends on what day it is.
    sender = 'mouse@fickle1.com'
    srsaddr = srs.forward(sender,'second.com')
    self.assertTrue(srsaddr.startswith(SRS.SRS0TAG))
    self.case_smashed = False
    srs.warn = self.warn
    addr = srs.reverse(srsaddr.lower())
    self.assertTrue(self.case_smashed)	# check that warn was called
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
    self.assertTrue(srsaddr.startswith(SRS.SRS0TAG))
    srsaddr1 = srs.forward(srsaddr,'third.com')
    #print srsaddr1
    self.assertTrue(srsaddr1.startswith(SRS.SRS0TAG))
    srsaddr2 = srs.forward(srsaddr1,'fourth.com')
    #print srsaddr2
    self.assertTrue(srsaddr2.startswith(SRS.SRS0TAG))
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
    #print(srsaddr)
    self.assertTrue(srsaddr.startswith(SRS.SRS0TAG))
    srsaddr1 = srs.forward(srsaddr,'third.com')
    #print(srsaddr1)
    self.assertTrue(srsaddr1.startswith(SRS.SRS0TAG))
    srsaddr2 = srs.forward(srsaddr1,'fourth.com')
    #print(srsaddr2)
    self.assertTrue(srsaddr2.startswith(SRS.SRS0TAG))
    addr = srs.reverse(srsaddr2)
    self.assertEqual(srsaddr1,addr)
    addr = srs.reverse(srsaddr1)
    self.assertEqual(srsaddr,addr)
    addr = srs.reverse(srsaddr)
    self.assertEqual(sender,addr)

  def run2(self): # handle two requests
    self.daemon.server.handle_request()
    self.daemon.server.handle_request()
    self.daemon.server.server_close()

  def sendcmd(self,*args):
    sock = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    sock.connect(self.sockname)
    sock.send(b' '.join(args)+b'\n')
    res = sock.recv(128).strip()
    sock.close()
    return res

  def testExim(self,sockname='/tmp/exsrsd',secret="shhhh!"):
    self.sockname = sockname
    self.daemon = Daemon(socket=sockname,secret=secret)
    server = threading.Thread(target=self.run2,name='srsd')
    server.start()
    sender = b'mouse@orig.com'
    srsaddr = self.sendcmd(b'FORWARD',sender,b'second.com')
    addr = self.sendcmd(b'REVERSE',srsaddr)
    server.join()
    self.assertEqual(sender,addr)

  def testSocketMap(self,sockname='/tmp/srsd',secret="shhhh!"):
    import pysrs,subprocess,time
    print()
    with open('test/pysrs.log','w') as fp:
      with subprocess.Popen(['./pysrs.py','test/pysrs.cfg'],stdout=fp) as p:
        time.sleep(1)
        try:
          m = SocketMap('/tmp/srsd')
          sender = 'mouse<@orig.com.>'
          # Sample req: 'make_srs unilit.us.\x9bstuart<@gathman.org.>'
          res,srsaddr = m.sendmap('make-srs','second.com',sender)
          res,addr = m.sendmap('reverse-srs',srsaddr)
        finally: m.close()
        p.terminate()
    self.assertEqual('OK',res)
    self.assertEqual(sender,addr)

  def testProgMap(self):
    import envfrom2srs
    import srs2envtol
    orig = 'mickey<@orig.com.>'
    newaddr = envfrom2srs.forward(orig)
    self.assertTrue(newaddr.endswith('.>'))
    addr2 = srs2envtol.reverse(newaddr)
    self.assertEqual(addr2,orig)
    # check case smashing by braindead mailers
    self.case_smashed = False
    srs2envtol.srs.warn = self.warn
    addr2 = srs2envtol.reverse(newaddr.lower())
    self.assertEqual(addr2,orig)
    self.assertTrue(self.case_smashed)

def suite(): 
  s = unittest.makeSuite(SRSTestCase,'test')
  s.addTest(makeSuite(SRSMilterTestCase,'test'))
  #s.addTest(doctest.DocTestSuite(bms))
  return s

if __name__ == '__main__':
  from sys import argv
  if len(argv) < 3:
    unittest.main()
  else:
    m = SocketMap('/tmp/srsd')
    r = m.sendmap(argv[1],*argv[2:])
    print(r)
    m.close()
