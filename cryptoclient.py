#CryptoBox client
import socket, ssl, os, hashlib, struct
from easyaes import encrypt, decrypt

class _globals():
    pass

def sha(x):
    return hashlib.sha512(x).digest()

def getemailandpasshash():
    email = raw_input("Enter email: ")
    password = raw_input("Enter password: ")
    passhash = sha(password)
    #pad email with 00000000 bytes for transmission; making it 64 bytes long
    email += chr(0)*(64-len(email))
    return email+passhash

def authenticate():
    message = chr(1)+chr(0)*3 #header
    message += getemailandpasshash()
    socket.send(message)

    reply = socket.recv(1)
    if ord(reply) == 1:
        print "Authentication successful"
        g.loggedin = True
    else:
        print "Authentication failed"

def new_account():
    message = chr(2)+chr(0)*3 #header
    message += getemailandpasshash()
    socket.send(message)

    reply = socket.recv(1)
    if ord(reply) == 1:
        print "New account created"
        g.loggedin = True
    else:
        print "Fail"
    

g = _globals()
g.loggedin = False

socket = socket.socket()
print "Connecting..."
socket.connect("85.211.57.20",7272)
print "Connected"

while True:
    print "1. Login"
    print "2. New account"
    inp = input("\n")
    if inp == 1:
        authenticate()
    elif inp == 2:
        
