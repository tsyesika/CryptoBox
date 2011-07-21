#CryptoBox client
import socket, ssl, os, hashlib, struct
from easyaes import encrypt, decrypt

def sha(x):
    return hashlib.sha512(x).digest()

socket = socket.socket()
print "Connecting..."
socket.connect("85.211.57.20",7272)
print "Connected"

email = raw_input("Enter email: ")
password = raw_input("Enter password: ")
passhash = sha(password)
#pad email with 00000000 bytes for transmission; making it 64 bytes long
email += chr(0)*(64-len(email))

message = chr(1)+chr(0)*3 #header
message += email+passhash
socket.send(message)

reply = socket.recv(1)
if ord(reply) == 1:
    print "Authentication successful"
else:
    print "Authentication failed"
