# Sendmail socket server daemon

import SocketServer

class MapError(Exception):
  def __init__(self,code,reason):
    self.code = code
    self.reason = reason

class Handler(SocketServer.StreamRequestHandler):

  def write(self,s):
    "write netstring to socket"
    self.wfile.write('%d:%s,' % (len(s),s))
    self.log(s)

  def _readlen(self,maxlen=8):
    "read netstring length from socket"
    n = ""
    file = self.rfile
    ch = file.read(1)
    while ch != ":":
      if not ch:
        raise EOFError
      if not ch in "0123456789":
        raise ValueError
      if len(n) >= maxlen:
	raise OverflowError
      n += ch
      ch = file.read(1)
    return int(n)

  def read(self, maxlen=None):
    "Read a netstring from the socket, and return the extracted netstring."
    n = self._readlen()
    if maxlen and n > maxlen:
      raise OverflowError
    file = self.rfile
    s = file.read(n)
    ch = file.read(1)
    if ch == ',':
      return s
    if ch == "":
      raise EOFError
    raise ValueError

  def handle(self):
    #self.log("connect")
    while True:
      try:
	line = self.read()
	self.log(line)
	args = line.split(' ',1)
	map = args.pop(0).replace('-','_')
	meth = getattr(self, '_handle_' + map, None)
	if not map:
	  raise ValueError("Unrecognized map: %s" % map)
	res = meth(*args)
	self.write('OK ' + res)
      except EOFError:
        #self.log("Ending connection")
	return
      except MapError,x:
	if code in ('PERM','TIMEOUT','NOTFOUND','OK','TEMP'):
	  self.write("%s %s"%(x.code,x.reason))
	else:
	  self.write("%s %s %s"%('PERM',x.code,x.reason))
      except LookupError,x:
        self.write("NOTFOUND")
      except Exception,x:
	#print x
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
    self.server = SocketServer.ThreadingUnixStreamServer(socket,handlerfactory)
    self.server.daemon = self

  def run(self):
    self.server.serve_forever()
