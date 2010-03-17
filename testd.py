# Simple test daemon
#
# Copyright (c) 2004-2010 Business Management Systems. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the same terms as Python itself.

from socket import *
import sys

sock = socket(AF_UNIX,SOCK_STREAM)
sock.connect('/tmp/srsd')
sock.send(' '.join(sys.argv[1:])+'\n')
res = sock.recv(128).strip()
print res
sock.close()
