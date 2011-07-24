##
# Server App
# Version 0.1
# Developed by Jessica T. & Philip J.
##

import socket, os, hashlib, thread, server_config, ssl, struct
from math import ceil as __ceil__


def sha(x):
        return hashlib.sha512(x).digest()

def makeheader(first,*args):
    """
    first should be an int in the range 0 <= first <= 255
    Any following arguments can be anything, and will be placed in consecutive header fields.
    """
    header = chr(first) + chr(200)*bool(args)
    for arg in args:
        if type(arg) == str:
            header += arg + chr(200)
        elif type(arg) == int:
            header += struct.pack("i",arg) + chr(200)
        elif type(arg) == float:
            header += struct.pack("f",arg) + chr(200)
        else:
            raise Exception("Unsupported type (can only pack strings, ints and floats")
    header += "|"
    return header

def ceil(x,y):
    """ Returns x/y rounded up to the nearest integer """
    return int(__ceil__(float(x)/y))

def authenticate(sock):
        ID = sock.recv(128) #receive email and password hash from client
        email = ID[:64]
        email = email[email.index(chr(0))] #shave off the padding
        passhash = ID[:64]
        #now check against the database
        sock.send(chr(1)) #YES MR TEST I CAN SEE FROM MY DATABASE THAT YOU DO INDEED OWN THIS ACCOUNT HERE HAVE SOME FILES

def new_account(sock):
        ID = sock.recv(128) #receive email and password hash from client
        email = ID[:64]
        email = email[email.index(chr(0))] #shave off the padding
        passhash = ID[:64]
        salt = os.urandom(32)
        storepass = sha(salt+passhash)
        #now put it in a database or something
        sock.send(chr(1)) #signal a successful account creation

def handle_send_request(sock,filesize):
        #make sure there's enough room on the server
        #xray, you handle this, i don't have a clue
        sock.send(chr(1)) #for now we'll just say yes

def receive_file(sock,path,exactsize):
    filebinary = download(sock,exactsize)
    #now do something with it. like put it in /home/useraccountid/path

def delete_file(sock,path):
        #delete it
        #let's not bother with an acknowledgement, I think we can assume this will be successful
        print "Received request to delete file", path
        pass

def move(sock,pathold,pathnew):
        #move the file
        print "Received request to move file"
        pass

def rename(sock,pathold,pathnew):
        #rename the file
        print "Received request to rename file"
        pass

def upload(data):
    """ Sends a large string data to the client, using sha to ensure integrity """
    # SEND HEAD
    exactlength = len(data)+ceil(len(data),256)*64
    print len(data), ceil(len(data),256), exactlength
    #      length of file   + number of hashes   *  64 bytes per hash
    message = makeheader(4,struct.pack("i",exactlength))
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
            resend = [struct.unpack("i",i) for i in resend.split(chr(200))[:-1]]
            break
    print "resend =", resend
    for i in resend:
        #resend corrupted blocks
        print "resending block", i
        upload(data[ i : min(i+256,len(data)) ])
    return len(resend)

def download(sock,exactsize):
    """ Receives a file, checking a hash after every 256 bytes """
    exactsize = struct.unpack("i",exactsize)[0]
    bytesreceived = 0
    resend = []
    bytestream = ""
    while bytesreceived < exactsize:
        block = sock.recv(min(exactsize-bytesreceived-64,256))
        HASH = sock.recv(64)
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
        message += struct.pack("i",i) + chr(200)
    message += "|"
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

def receive_header(sock):
    header = ""
    while True:
        header += sock.recv(1)
        if header == "#":
                raise
        if header[-1] == "|":
            #found end of header
            args = header.split(chr(200))[1:-1]
            return ord(header[0]), args

def Connection_Handler(sock):
    """ Handles new connections to server """
    while True:
        print "Waiting for a header..."
        TYPE, args = receive_header(sock)
        print "got header", TYPE, args
        handlers[TYPE](sock,*args)
        print "dealt with"

handlers = {
        1:authenticate,
        2:new_account,
        3:handle_send_request,
        4:receive_file,
        5:delete_file
        }

if __name__ == "__main__":
    # Setup port
    if server_config.ipv6:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    else:
        sock = socket.socket()
        sock.bind(('localhost',7282))
        sock.listen(5)
    while True:
        print sock
        clientsock, addr = sock.accept()
        if server_config.sslwrap:
            sock = ssl.wrap_socket(sock, server_side=True, ssl_version=ssl.PROTOCOL_TLSv1)
        Connection_Handler(clientsock)
        #thread.start_new_thread(Connection_Handler, (clientsock,))
