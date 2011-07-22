#CryptoBox client
import socket, ssl, os, hashlib, struct
import easyaes
from math import ceil

class _globals():
    pass

def makeheader(first,*args):
    """
    first should be an int in the range 0 <= first <= 255
    Any following arguments can be anything, and will be placed in consecutive header fields.
    """
    header = chr(first) + ":"*bool(args)
    for arg in args:
        if type(arg) == str:
            header += arg + ":"
        elif type(arg) == int:
            header += struct.pack("i",arg) + ":"
        elif type(arg) == float:
            header += struct.pack("f",arg) + ":"
        else:
            raise Exception("Unsupported type (can only pack strings, ints and floats")
    header += "|"
    return header

def sha(x):
    return hashlib.sha512(x).digest()

def getemailandpasshash():
    email = raw_input("Enter email: ")
    password = raw_input("Enter password: ")
    g.password = password #this is hackish. Do not like.
    passhash = sha(password)
    #pad email with 00000000 bytes for transmission; making it 64 bytes long
    email += chr(0)*(64-len(email))
    return email+passhash

def authenticate():
    message = makeheader(1)
    message += getemailandpasshash()
    socket.send(message)

    reply = socket.recv(1)
    if ord(reply) == 1:
        print "Authentication successful"
        g.loggedin = True
    else:
        print "Authentication failed"

def new_account():
    message = makeheader(2)
    message += getemailandpasshash()
    socket.send(message)

    reply = socket.recv(1)
    if ord(reply) == 1:
        print "New account created"
        g.loggedin = True
    else:
        print "Fail"
    
def upload():
    path = raw_input("Enter path to file:\n")
    length = int(ceil(os.stat(path).st_size/16.0)) #now length is number of blocks
    message = makeheader(3,struct.pack("i",length)) #add a block to length, just to be safe
    socket.send(message) #send request has no body
    reply = socket.recv(1)
    if ord(reply) != 1:
        print "Upload request denied. Sorry."
        return
    
    ciphertext = []
    ivkey = os.urandom(16)
    iv = sha(ivkey+g.password)
    fin = open(path,"rb")
    h = sha(fin.read())
    fin.close()
    fout = open("iv_table.txt","a")
    fout.write(h+":"+ivkey+"\n") #store the ivkey for decrypting the file later
    fout.close()

    easyaes.encrypt(path,ciphertext,iv)
    # SEND HEAD
    exactlength = struct.calcsize("L")+64+(len(ciphertext)-1)*16 + int(ceil(len(ciphertext)/16.0))*64
    #            lengthmarker +lengthmarkerhash + ciphertext + ciphertexthashes
    message = makeheader(4,struct.pack("i",exactlength))
    socket.send(message)
    # SEND BODY
    socket.send(ciphertext[0]) #plaintext length marker
    socket.send(sha(ciphertext[0])) #hash of marker
    cursor = 1
    while cursor < len(ciphertext):
        if len(ciphertext[cursor:]) >= 16:
            block = "".join(ciphertext[cursor:cursor+16])
        else:
            block = "".join(ciphertext[cursor:])
        socket.send(block)
        socket.send(sha(block))
        cursor += 16
    

#message header 1st bytes:
#1 - authentication request
#2 - new account request
#3 - send request
#4 - incoming file (next four bytes store number of 16-byte blocks in file as an unsigned short

g = _globals()
g.loggedin = False

socket = socket.socket()
print "Connecting..."
socket.connect(("85.211.57.20",7272))
print "Connected"

while True:
    print "1. Login"
    print "2. New account"
    print "3. Upload file"
    inp = input("\n")
    if inp == 1:
        authenticate()
    elif inp == 2:
        new_account()
    elif inp == 3:
        upload()
