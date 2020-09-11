# Copyright (c) 2004-2010 Business Management Systems. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the same terms as Python itself.
#
# Base class for sendmail socket servers

try:
  import socketserver
except:
  import SocketServer as socketserver

class MapError(Exception):
  def __init__(self,code,reason):
    self.code = code
    self.reason = reason

class Handler(socketserver.StreamRequestHandler):

  def write(self,s):
    "write netstring to socket"
    self.wfile.write(b'%d:%s,' % (len(s),s.encode()))
    self.log(s)

  def _readlen(self,maxlen=8):
    "read netstring length from socket"
    n = b''
    rfile = self.rfile
    ch = rfile.read(1)
    while ch != b':':
      if not ch:
        raise EOFError
      if not ch in b'0123456789':
        raise ValueError
      if len(n) >= maxlen:
        raise OverflowError
      n += ch
      ch = rfile.read(1)
    return int(n)

  def read(self, maxlen=None):
    "Read a netstring from the socket, and return the extracted netstring."
    n = self._readlen()
    if maxlen and n > maxlen:
      raise OverflowError
    file = self.rfile
    s = file.read(n)
    ch = file.read(1)
    if ch == b',':
      return s
    if ch == b'':
      raise EOFError
    raise ValueError

  def handle(self):
    #self.log("connect")
    while True:
      try:
        line = self.read()
        self.log(repr(line))
        args = line.split(b' ',1)
        mapname = args.pop(0).decode().replace('-','_')
        meth = getattr(self, '_handle_' + mapname, None)
        if not map:
          raise ValueError("Unrecognized map: %s" % mapname)
        res = meth(*args)
        self.write('OK ' + res)
      except EOFError:
        #self.log("Ending connection")
        return
      except MapError as x:
        if code in ('PERM','TIMEOUT','NOTFOUND','OK','TEMP'):
          self.write("%s %s"%(x.code,x.reason))
        else:
          self.write("%s %s %s"%('PERM',x.code,x.reason))
      except LookupError as x:
        self.write("NOTFOUND")
      except Exception as x:
        #print(x)
        self.write("TEMP %s"%x)
      # PERM,TIMEOUT

# Application should subclass SocketMap.Daemon, and define
# a _handler_map_name method for each sendmail socket map handled
# by this server.  The socket is a unix domain socket which must match
# the socket defined in sendmail.cf.
#
# Socket maps in sendmail.cf look like this:

# Kmy_map socket local:/tmp/sockd

class Daemon(object):

  def __init__(self,socket,handlerfactory):
    self.socket = socket
    try:
      os.unlink(socket)
    except: pass
    self.server = socketserver.ThreadingUnixStreamServer(socket,handlerfactory)
    self.server.daemon = self

  def run(self):
    self.server.serve_forever()
