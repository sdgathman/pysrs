#!/usr/bin/python2
#
# A simple SRS milter for Sendmail-8.14/Postfix-?
#
# NOTE: use with pysrs socketmap and sendmail-cf macro to handle
# multiple recipients.
#
# The logical problem is that a milter gets to change MFROM only once for
# multiple recipients.  When there is a conflict between recipients, we
# either have to punt (all SRS or all no-SRS) or resubmit some of the
# recipients to "split" the message.
#
# The sendmail cf package, in contrast, gets invoked for every recipient.

# http://www.sendmail.org/doc/sendmail-current/libmilter/docs/installation.html

# Author: Stuart D. Gathman <stuart@gathman.org>
# Copyright 2007 Business Management Systems, Inc.
# Copyright 2017 Stuart D. Gathman
# This program is free software; you can redistribute it and/or modify
# it under the same terms as Python itself.

import SRS
import SES
import sys
import Milter
import syslog
import re
from Milter.config import MilterConfigParser
from Milter.utils import iniplist,parse_addr

syslog.openlog('srsmilter',0,syslog.LOG_MAIL)

class Config(object):
  "Hold configuration options."
  def __init__(conf,cfglist):
    cp = MilterConfigParser()
    cp.read(cfglist)
    if cp.has_option('srsmilter','datadir'):
      os.chdir(cp.get('srsmilter','datadir'))      # FIXME: side effect!
    conf.socketname = cp.getdefault('srsmilter','socketname',
        '/var/run/milter/srsmilter')
    conf.miltername = cp.getdefault('srsmilter','name','pysrsfilter')
    conf.trusted_relay = cp.getlist('srsmilter','trusted_relay')
    conf.miltersrs = cp.getboolean('srsmilter','miltersrs')
    conf.internal_connect = cp.getlist('srsmilter','internal_connect')
    conf.srs_reject_spoofed = cp.getboolean('srsmilter','reject_spoofed')
    conf.trusted_forwarder = cp.getlist('srs','trusted_forwarder')
    conf.secret = cp.getdefault('srs','secret','shhhh!')
    conf.maxage = cp.getintdefault('srs','maxage',21)
    conf.hashlength = cp.getintdefault('srs','hashlength',5)
    conf.separator = cp.getdefault('srs','separator','=')
    conf.database = cp.getdefault('srs','database')
    conf.nosrsdomain = cp.getlist('srs','nosrs') # no SRS rcpt
    conf.banned_users = cp.getlist('srs','banned_users')
    conf.srs_domain = set(cp.getlist('srs','srs')) # check rcpt 
    conf.sesdomain = set(cp.getlist('srs','ses')) # sign from with ses
    conf.signdomain = set(cp.getlist('srs','sign')) # sign from with srs
    conf.fwdomain = cp.getdefault('srs','fwdomain',None) # forwarding domain
    if conf.database:
      global SRS
      import SRS.DB
      conf.srs = SRS.DB.DB(database=conf.database,secret=conf.secret,
        maxage=conf.maxage,hashlength=conf.hashlength,separator=conf.separator)
    else:
      conf.srs = SRS.Guarded.Guarded(secret=conf.secret,
        maxage=conf.maxage,hashlength=conf.hashlength,separator=conf.separator)
    if SES:
      conf.ses = SES.new(secret=conf.secret,expiration=conf.maxage)
      conf.srs_domain = set(conf.sesdomain)
      conf.srs_domain.update(conf.srs_domain)
    else:
      conf.srs_domain = set(conf.srs_domain)
    conf.srs_domain.update(conf.signdomain)
    if conf.fwdomain:
      conf.srs_domain.add(conf.fwdomain)

class srsMilter(Milter.Base):
  "Milter to check SRS.  Each connection gets its own instance."

  def log(self,*msg):
    syslog.syslog('[%d] %s' % (self.id,' '.join([str(m) for m in msg])))

  def __init__(self):
    self.mailfrom = None
    self.id = Milter.uniqueID()
    # we don't want config used to change during a connection
    self.conf = config

  bracketRE = re.compile(r'^<|>$|\.>$')
  srsre = re.compile(r'^SRS[01][+-=]',re.IGNORECASE)

  def make_srs(self,old_address):
    h = self.receiver
    nosrsdomain = self.conf.nosrsdomain
    if old_address == '<>' or not h or h in nosrsdomain:
      return old_address
    srs = self.conf.srs
    ses = self.conf.ses
    fwdomain = self.conf.fwdomain
    sesdomain = self.conf.sesdomain
    signdomain = self.conf.signdomain
    use_address = self.bracketRE.sub('',old_address)

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
        return '<%s>'%new_address
      except:
        return old_address

  @Milter.noreply
  def connect(self,hostname,unused,hostaddr):
    self.internal_connection = False
    self.trusted_relay = False
    # sometimes people put extra space in sendmail config, so we strip
    self.receiver = self.getsymval('j').strip()
    if hostaddr and len(hostaddr) > 0:
      ipaddr = hostaddr[0]
      if iniplist(ipaddr,self.conf.internal_connect):
        self.internal_connection = True
      if iniplist(ipaddr,self.conf.trusted_relay):
        self.trusted_relay = True
    else: ipaddr = ''
    self.connectip = ipaddr
    if self.internal_connection:
      connecttype = 'INTERNAL'
    else:
      connecttype = 'EXTERNAL'
    if self.trusted_relay:
      connecttype += ' TRUSTED'
    self.log("connect from %s at %s %s" % (hostname,hostaddr,connecttype))
    return Milter.CONTINUE

  @Milter.noreply
  def envfrom(self,f,*str):
    self.log("mail from",f,str)
    self.mailfrom = f
    t = parse_addr(f)
    if len(t) == 2: t[1] = t[1].lower()
    self.canon_from = '@'.join(t)
    self.srsrcpt = []
    self.nosrsrcpt = []
    self.redirect_list = []
    self.discard_list = []
    self.is_bounce = (f == '<>' or t[0].lower() in self.conf.banned_users)
    self.data_allowed = True
    return Milter.CONTINUE

  ## Accumulate deleted recipients to be applied in eom callback.
  def del_recipient(self,rcpt):
    rcpt = rcpt.lower()
    if not rcpt in self.discard_list:
      self.discard_list.append(rcpt)

  ## Accumulate added recipients to be applied in eom callback.
  def add_recipient(self,rcpt,params):
    rcpt = rcpt.lower()
    if not rcpt in (r[0] for r in self.redirect_list):
      self.redirect_list.append((rcpt,params))

  def envrcpt(self,to,*params):
    conf = self.conf
    t = parse_addr(to)
    if len(t) == 2:
      t[1] = t[1].lower()
      user,domain = t
      if self.is_bounce and domain in conf.srs_domain:
        # require valid signed recipient
        oldaddr = '@'.join(parse_addr(to))
        try:
          if conf.ses:
            newaddr = ses.verify(oldaddr)
          else:
            newaddr = oldaddr,
          if len(newaddr) > 1:
            newaddr = newaddr[0]
            self.log("ses rcpt:",newaddr)
          else:
            newaddr = srs.reverse(oldaddr)
            self.log("srs rcpt:",newaddr)
          self.del_recipient(to)
          self.add_recipient('<%s>',newaddr,params)
        except:
          # no valid SRS signature
          if not (self.internal_connection or self.trusted_relay):
            # reject specific recipients with bad sig
            if self.srsre.match(oldaddr):
              self.log("REJECT: srs spoofed:",oldaddr)
              self.setreply('550','5.7.1','Invalid SRS signature')
              return Milter.REJECT
            if oldaddr.startswith('SES='):
              self.log("REJECT: ses spoofed:",oldaddr)
              self.setreply('550','5.7.1','Invalid SES signature')
              return Milter.REJECT
            # reject message for any missing sig
            self.data_allowed = not conf.srs_reject_spoofed
      else:
        # sign "outgoing" from
        if domain in self.conf.nosrsdomain:
          self.nosrsrcpt.append(to)
        else:
          self.srsrcpt.append(to)
    else:       # no SRS for unqualified recipients
      self.nosrsrcpt.append(to)
    return Milter.CONTINUE

  def data(self):
    if not self.data_allowed:
      return Milter.REJECT
    return Milter.CONTINUE

  def eom(self):
    # apply recipient changes
    for to in self.discard_list:
      self.delrcpt(to)
    for to,p in self.redirect_list:
      self.addrcpt(to,p)
    # optionally, do outgoing SRS for all recipients
    if self.conf.miltersrs and self.srsrcpt:
      newaddr = self.make_srs(self.canon_from)
      if newaddr != self.canon_from:
        self.chgfrom(newaddr)
    return Milter.CONTINUE

if __name__ == "__main__":
  global config
  config = Config(['pysrs.cfg','/etc/mail/pysrs.cfg'])
  Milter.factory = srsMilter
  if config.miltersrs:
    flags = Milter.CHGFROM + Milter.DELRCPT
  else:
    flags = Milter.DELRCPT
  Milter.set_flags(Milter.CHGFROM + Milter.DELRCPT)
  miltername = config.miltername
  socketname = config.socketname
  print("""To use this with sendmail, add the following to sendmail.cf:

O InputMailFilters=%s
X%s,        S=local:%s

See the sendmail README for libmilter.
sample srsmilter startup""" % (miltername,miltername,socketname))
  sys.stdout.flush()
  Milter.runmilter(miltername,socketname,240)
  print("srsmilter shutdown")
