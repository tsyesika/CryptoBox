#transfer.py
#a module providing file transfer routines for both client and server
import easyaes, time, hashlib, os
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
    header = chr(first) + chr(0)*bool(args)
    for arg in args:
        if type(arg) == str:
            header += arg + chr(0)
        elif type(arg) == int or type(arg) == float:
            header += str(arg) + chr(0)
        else:
            raise Exception("Unsupported type (can only send strings, ints and floats")
    header += chr(255) #i'd really prefer to use something like : and | as delimiters, but since there doesn't seem to be a single character that doesn't appear in file paths on any system, I'm using non-printable characters
    return header

def request_send(path,exactsize=None):
    if not exactsize:
            length = ceil(os.stat(path).st_size,16)*16 + 256 #now length is a generous estimate of ciphertext filesize
            message = makeheader(3,length)
            socket.send(message) #send request has no body
    else:
            socket.send(makeheader(3,exactsize))
    reply = socket.recv(1)
    if ord(reply) != 1:
        print "Upload request denied. Sorry."
        return False
    return True

def handle_send_request(sock,filesize):
        #make sure there's enough room on the server
        #xray, you handle this, i don't have a clue
        filesize = int(filesize)
        sock.send(chr(1)) #for now we'll just say yes

def send_file(path):
    cipher = []
    print "Encrypting..."
    easyaes.encrypt(path,cipher,g.password) #easyaes needs your password to make an IV)
    print "Done"
    cipher = "".join(cipher)
    
    exactlength = len(cipher)+ceil(len(cipher),256)*64
    print len(cipher), ceil(len(cipher),256)*64
    #       length of file    + number of hashes   *  64 bytes per hash
    # SEND HEAD
    message = makeheader(4,path,exactlength)
    socket.send(message)
    # SEND BODY
    r = upload(cipher)
    print "File sent,", r, "blocks resent"

def receive_file(sock,path,exactsize):
    filebinary = download(sock,exactsize)
    #now do something with it. like put it in /home/useraccountid/path

def delete_file(sock,path):
        #delete it
        #let's not bother with an acknowledgement, I think we can assume this will be successful
        print "Received request to delete file", path
        pass

def move_file(sock,pathold,pathnew):
        #move the file
        print "Received request to move file"
        pass

def rename_file(sock,pathold,pathnew):
        #rename the file
        print "Received request to rename file"
        pass

def upload(data):
    """ Sends a large string data to the server, using sha to ensure integrity """ 
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
    resend = ""
    while True:
        resend += socket.recv(1)
        if resend[-1] == chr(255):
            print resend
            resend = [int(i) for i in resend.split(chr(0))[:-1]]
            break
    print "resend =", resend
    for i in resend:
        #resend corrupted blocks
        print "resending block", i
        socket.send(
            makeheader(4, min(256,len(data)-i))
            )
        upload(data[ i : min(i+256,len(data)) ])
    return len(resend)

def download(sock,exactsize):
    """ Receives a file, checking a hash after every 256 bytes """
    print "download running from transfer namespace"
    exactsize = int(exactsize)
    bytesreceived = 0
    resend = []
    bytestream = ""
    time.sleep(1)
    while bytesreceived < exactsize:
        block = sock.recv(min(exactsize-bytesreceived-64,256))
        HASH = sock.recv(64)
        #print "got block", len(block), len(HASH)
        #check block
        if sha(block) != HASH:
            #add a resend request
            print "hash doesn't match"
            resend.append(bytesreceived - 64*bytesreceived / 320) #working out where the corrupted block started in the original data (without hashes)
        bytestream += block #don't worry, we'll request a resend and overwrite it if it was corrupted
        bytesreceived += 256+64
    print len(resend), "out of", ceil(exactsize,256), "blocks corrupted"
    message = ""
    for i in resend: #i for index (in the original, unhashed bytestream back on clientside)
        raise
        message += str(i) + chr(0)
    message += chr(255)
    sock.send(message)
    print "sent acknowledgement:", message
    for i in resend:
        #now receive the resends, if any
        print "getting resend", i
        exactsize = receive_header(sock)[1][0]
        block = download(sock,exactsize)
        print "got resend"
        #now insert the correct block back into the bytestream, overwriting the corrupted block
        bytestream = bytestream[:i]+block+bytestream[i+256:]
    return bytestream

g = _globals()
