#CryptoBox client
import socket, ssl, os, hashlib, struct
import easyaes
from math import ceil as __ceil__

class _globals():
    pass

def sha(x):
    return hashlib.sha512(x).digest()

def ceil(x,y):
    """ Returns x/y rounded up to the nearest integer """
    return int(__ceil__(float(x)/y))

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
    
def upload(data):
    """ Sends a large string data to the server, using sha to ensure integrity """
    # SEND HEAD
    exactlength = len(data)+ceil(len(data),256)*64
    #           length of file   + number of hashes   *  64 bytes per hash
    message = makeheader(4,struct.pack("i",data))
    socket.send(message)
    # SEND BODY
    cursor = 0
    while cursor < len(data):
        if len(data) - cursor >= 256:
            block = data[cursor:cursor+256]
        else:
            block = data[cursor:]
        socket.send(block)
        socket.send(sha(block))
        cursor += 256

    #wait for acknowledgement from server
    while True:
        resend = ""
        resend += socket.recv(1)
        if resend[-1] == "|":
            resend = [struct.unpack("i",i) for i in resend.split(":")[:-1]]
            break
        
    for i in resend:
        #resend corrupted blocks
        upload(data[ i : min(i+256,len(data)) ])
    return len(resend)

#message header 1st bytes:
#1 - authentication request
#2 - new account request
#3 - send request (followed by approximate file size)
#4 - incoming file (next four bytes store number of 16-byte blocks in file as an integer)
g = _globals()
g.loggedin = False

socket = socket.socket()
print "Connecting..."
socket.connect(("localhost",7272))
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
        path = raw_input("Enter path to file:\n")
        length = int(ceil(os.stat(path).st_size/16.0)) #now length is number of blocks
        message = makeheader(3,struct.pack("i",length)) #add a block to length, just to be safe
        socket.send(message) #send request has no body
        reply = socket.recv(1)
        if ord(reply) != 1:
            print "Upload request denied. Sorry."
            return

        #ENCRYT FILE, STORE IV KEY
        ivkey = os.urandom(16)
        iv = sha(ivkey+g.password)
        fin = open(path,"rb")
        h = sha(fin.read())
        fin.close()
        fout = open("iv_table.txt","a")
        fout.write(h+":"+ivkey+"\n") #store the ivkey for decrypting the file later
        fout.close()
        ciphertext = []
        easyaes.encrypt(path,ciphertext,iv)
        ciphertext = "".join(ciphertext)
        
        r = upload(ciphertext)
        print "File sent,", r, "blocks resent"
