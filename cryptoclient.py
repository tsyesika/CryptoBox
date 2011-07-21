#CryptoBox client
import socket, ssl, os, hashlib, struct
from easyaes import encrypt, decrypt

socket = socket.socket()
print "Connecting..."
socket.connect("85.211.57.20",4554)
print "Connected"

email = raw_input("Enter email: ")
password = raw_input("Enter password: ")
passhash = hashlib.sha512(password).digest()
#pad email with 00000000 bytes for transmission; making it 64 bytes long
email += ord(0)*(64-len(email))

socket.send(email+passhash)
reply = socket.recv(1)
if ord(reply) == 1:
    print "Authentication successful"
else:
    print "Authentication failed"
