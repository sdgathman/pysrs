from socket import *
import sys

sock = socket(AF_UNIX,SOCK_STREAM)
sock.connect('/tmp/srsd')
sock.send(' '.join(sys.argv[1:])+'\n')
res = sock.recv(128).strip()
print res
sock.close()
