# A simple SRS milter for Sendmail-8.14/Postfix-?

#
# INCOMPLETE!!
#
# The logical problem is that a milter gets to change MFROM only once for
# multiple recipients.  When there is a conflict between recipients, we
# either have to punt (all SRS or all no-SRS) or resubmit some of the
# recipients to "split" the message.
#
# The sendmail cf package, in contrast, gets invoked for every recipient.

# http://www.sendmail.org/doc/sendmail-current/libmilter/docs/installation.html

# Author: Stuart D. Gathman <stuart@bmsi.com>
# Copyright 2007 Business Management Systems, Inc.
# This program is free software; you can redistribute it and/or modify
# it under the same terms as Python itself.

import SRS
import SES
import sys
import Milter
import spf
import syslog
from Milter.config import MilterConfigParser
from Milter.utils import iniplist,parse_addr

syslog.openlog('srsmilter',0,syslog.LOG_MAIL)

class Config(object):
  "Hold configuration options."
  def __init__(conf,cfglist):
    cp = MilterConfigParser()
    cp.read(cfglist)
    if cp.has_option('milter','datadir'):
      os.chdir(cp.get('milter','datadir'))      # FIXME: side effect!
    conf.socketname = cp.getdefault('milter','socketname',
        '/var/run/milter/pysrs')
    conf.miltername = cp.getdefault('milter','name','pysrsfilter')
    conf.trusted_relay = cp.getlist('milter','trusted_relay')
    conf.internal_connect = cp.getlist('milter','internal_connect')
    conf.trusted_forwarder = cp.getlist('srs','trusted_forwarder')
    conf.secret = cp.getdefault('srs','secret','shhhh!')
    conf.maxage = cp.getintdefault('srs','maxage',21)
    conf.hashlength = cp.getintdefault('srs','hashlength',5)
    conf.separator = cp.getdefault('srs','separator','=')
    conf.database = cp.getdefault('srs','database')
    conf.srs_reject_spoofed = cp.getboolean('srs','reject_spoofed')
    conf.nosrsdomain = cp.getlist('srs','nosrs') # no SRS rcpt
    conf.banned_users = cp.getlist('srs','banned_users')
    conf.srs_domain = set(cp.getlist('srs','srs')) # check rcpt 
    conf.sesdomain = set(cp.getlist('srs','ses')) # sign from with ses
    conf.signdomain = set(cp.getlist('srs','sign')) # sign from with srs
    conf.fwdomain = cp.getdefault('srs','fwdomain',None) # forwarding domain
    if database:
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
  def add_recipient(self,rcpt):
    rcpt = rcpt.lower()
    if not rcpt in self.redirect_list:
      self.redirect_list.append(rcpt)

  def envrcpt(self,to,*str):
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
          self.add_recipient('<%s>',newaddr)
        except:
          # no valid SRS signature
          if not (self.internal_connection or self.trusted_relay):
            if self.srsre.match(oldaddr):
              self.log("REJECT: srs spoofed:",oldaddr)
              self.setreply('550','5.7.1','Invalid SRS signature')
              return Milter.REJECT
            if oldaddr.startswith('SES='):
              self.log("REJECT: ses spoofed:",oldaddr)
              self.setreply('550','5.7.1','Invalid SES signature')
              return Milter.REJECT
            self.data_allowed = not conf.srs_reject_spoofed
      else:
        # sign "outgoing" from
        if domain in nosrsdomain:
          self.nosrsrcpt.append(to)
        else:
          self.srsrcpt.append(to)
    else:       # no SRS for unqualified recipients
      self.nosrsrcpt.append(to)
    return Milter.CONTINUE

  def eom(self):
    for name,val,idx in self.new_headers:
      try:
	self.addheader(name,val,idx)
      except:
	self.addheader(name,val)	# older sendmail can't insheader
    return Milter.CONTINUE

if __name__ == "__main__":
  Milter.factory = srsMilter
  Milter.set_flags(Milter.CHGFROM + Milter.DELRCPT)
  global config
  config = Config(['spfmilter.cfg','/etc/mail/spfmilter.cfg'])
  miltername = config.miltername
  socketname = config.socketname
  print """To use this with sendmail, add the following to sendmail.cf:

O InputMailFilters=%s
X%s,        S=local:%s

See the sendmail README for libmilter.
sample srsmilter startup""" % (miltername,miltername,socketname)
  sys.stdout.flush()
  Milter.runmilter("pysrsfilter",socketname,240)
  print "sample srsmilter shutdown"
