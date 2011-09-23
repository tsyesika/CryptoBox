##
# Server App
# Version 0.1
# Developed by Jessica T. & Philip J.
##

import socket, os, hashlib, thread, server_config, ssl, time, common, traceback, shutil, struct
from common import makeheader, ceil

# if config.database_type == "mysql":
#	import db.mysql as db
# elif config.database_type == "sqlite":
#	import db.sqlite as db
# elif config.database_type == "pickle":
#	import db.pickle as db
# else:
# 	raise # some kinda error as no database has been selected?

class Halfsock():
    """A wrapper class for socket that receives from a buffer list instead of the directly from socket.
    Also will not send until the socket is free, ensuring threads don't send at the same time."""
    def __init__(self,sock,_thread):
        self.sock = sock
        self._thread = _thread #1 = watcher, 2 = listener
        
    def recv(self,n):
        message = ""
        if self._thread == 1:
            Buffer = watchersockbuffer[self.sock]
        else:
            Buffer = listenersockbuffer[self.sock]
        while len(message) < n:
            if Buffer:
                message += "".join(Buffer[:n])
                del Buffer[:n]
            else:
                time.sleep(0.1) #don't devour the CPU
        return message

    def send(self,message,recipient='l'):
        if type(recipient) == int:
            recipient = ('w','l')[recipient]
        while socklock[self.sock]:
            time.sleep(0.1)
        socklock[self.sock] = self._thread
        self.sock.send(recipient+struct.pack("H",len(message)))
        self.sock.send(message)
        socklock[self.sock] = 0
        if self.sock == debugsock:
            if self._thread == 1:
                wsend.extend(list(recipient+struct.pack("H",len(message))+message))
            else:
                lsend.extend(list(recipient+struct.pack("H",len(message))+message))


def sha(x):
    return hashlib.sha512(x).digest()

def crash(sock):
    global die
    die = True
    sock.close()
    thread.interrupt_main()
    x = socklock[3] #raise

def authenticate(sock):
    try:
        ID = sock.recv(128) #receive email and password hash from client
        email = ID[:64]
        email = email[:email.index(chr(0))] #shave off the padding
        passhash = ID[:64]
                
                # salt = db.getsalt(dbc, email)
                # if salt[0]: salt = salt[0]
                # else: #incorrect :(

        passhash = sha(passhash) # + salt?  #yeah
                #now check against the database

                # res = db.login(dbc, email, pass)
                # if res[0]:
                        # Correct
                # else:
                        # Incorrect
                        
        #assuming valid password:

        watchersock = Halfsock(sock,1)
        listenersock = Halfsock(sock,2)
        if email in groups:
            #one or more clients of this account are already logged in
            groups[email].add((watchersock,listenersock))
        else:
            groups[email] = set([(watchersock,listenersock)])
        print groups
        relaybuffer[watchersock] = []
        socklock[sock] = 0 #0 = no lock, 1 = locked to watcher, 2 = locked to listener
        watchersockbuffer[sock] = []
        listenersockbuffer[sock] = []
        
        sock.send(chr(1)) #YES MR TEST I CAN SEE FROM MY DATABASE THAT YOU DO INDEED OWN THIS ACCOUNT HERE HAVE SOME FILES
        thread.start_new_thread(watcher,(watchersock,) )
        thread.start_new_thread(listener,(listenersock,) )
        receiver(sock)
    except:
        traceback.print_exc()
        thread.interrupt_main()

def receive_header(sock):
    header = ""
    while True:
        header += sock.recv(1)
        if header == "#":
            #print "HERP FUCKING DERP"
            global die
            die = True
            sock.close()
            serversock.close()
            thread.interrupt_main()
            raise Exception("HERP FUCKING DERP")
        if header[-1] == chr(255):
            #found end of header
            args = header.split(chr(0))[1:-1]
            return ord(header[0]), args

def sock_email(sock):
    """Returns the email address of the user of the client that sock is connected to"""
    for email in groups:
        if [pair for pair in groups[email] if sock in pair]:
            return email

def repopath(sock):
    """Returns a path to sock's account's repo folder"""
    reponame = sock_email(sock).replace("@","at").replace(".","dot")
    return "C:\\Users\\Philip\\Desktop\\store\\" + reponame

def watcher(sock):
    """
    Watches for changes to sock's relaybuffer that have been posted by other listener threads
    """
    try:
        while True:
            if die:
                return
            time.sleep(0.1) #don't devour the CPU
            if relaybuffer[sock]:
                while relaybuffer[sock]:
                    message = relaybuffer[sock].pop(0)
                    relay(sock,message[0],message[1])
    except:
        #print "DERP"
        traceback.print_exc()
        crash()

#---------------- SEND MOD REQUESTS -----------

def relay(sock,command,args):
    if command == 2:
        #a folder was made
        message = makeheader(2,args[0])
        sock.send(message)
    if command == 4:
        #a file was added to a folder; now add it to yours
        if request_send(sock,exactsize=int(args[1])+256):
            send_file(sock,args[0])
    elif command == 5:
        #a file was deleted from a folder; now delete it from yours
        message = makeheader(5,args[0])
        sock.send(message)
    elif command == 6:
        #a file was moved in a folder; now move it in yours
        message = makeheader(6,args[0],args[1])
        sock.send(message)
    elif command == 7:
        #a file was renamed in a folder; now rename it in yours
        message = makeheader(7,args[0],args[1])
        sock.send(message)

def request_send(sock,path=None,exactsize=None):
    if not exactsize:
        #print "Requesting to send", path
        length = ceil(os.stat(path).st_size,16)*16 + 256 #now length is a generous estimate of ciphertext filesize
        message = makeheader(3,length)
        sock.send(message) #send request has no body
    else:
        #print "Requesting to send", exactsize, "bytes"
        sock.send(makeheader(3,exactsize))
    reply = sock.recv(1)
    if ord(reply) != 1:
        #print "Upload request denied. Sorry."
        return False
    else:
        #print "Request was accepted, proceeding to send"
        return True

def send_file(sock,path):
    fin = open(repopath(sock)+"\\"+path,"rb")
    data = fin.read()
    exactlength = len(data)+ceil(len(data),256)*64
    #       length of file    + number of hashes   *  64 bytes per hash
    # SEND HEAD
    message = makeheader(4,path,exactlength)
    sock.send(message)
    # SEND BODY
    r = upload(sock,data)
    #print "File sent:", os.path.split(path)[1]+",", r, "blocks resent"

def upload(socket,data):
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
            resend = [int(i) for i in resend.split(chr(0))[:-1]]
            break
    for i in resend:
        #resend corrupted blocks
        #print "resending block", i
        socket.send(
            makeheader(4, min(256,len(data)-i))
            )
        upload(data[ i : min(i+256,len(data)) ])
    return len(resend)

#---------------- /SEND MOD REQUESTS ----------



#------- HANDLE MOD REQUESTS ------------------

def make_folder(sock,path):
    print "Received request to make folder", path
    path = os.path.join(repopath(sock),path)
    os.mkdir(path)

def handle_send_request(sock,filesize):
    #make sure there's enough room on the server
    print "Received space check request for", filesize, "bytes"
    filesize = int(filesize)
    sock.send(chr(1),'w') #for now we'll just say yes

def receive_file(sock,path,exactsize):
    filebinary = download(sock,exactsize)
    print "File received:", os.path.split(path)[1]
    fout = open(repopath(sock)+"\\"+path,"wb")
    fout.write(filebinary)
    fout.close()

def download(sock,exactsize):
    """ Receives a file, checking a hash after every 256 bytes """
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
    message = ""
    for i in resend: #i for index (in the original, unhashed bytestream back on clientside)
        raise
        message += str(i) + chr(0)
    message += chr(255)
    sock.send(message,'w')
    for i in resend:
        #now receive the resends, if any
        print "getting resend", i
        exactsize = receive_header(sock)[1][0]
        block = download(sock,exactsize)
        print "got resend"
        #now insert the correct block back into the bytestream, overwriting the corrupted block
        bytestream = bytestream[:i]+block+bytestream[i+256:]
    print exactsize, "bytes received"
    return bytestream

def delete_file(sock,path):
    #delete it
    #let's not bother with an acknowledgement, I think we can assume this will be successful
    print "Received request to delete file", path
    path = os.path.join(repopath(sock),path)
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)

def move_file(sock,pathold,pathnew):
    #move the file
    print "Received request to move file"
    pathold = os.path.join(repopath(sock),pathold)
    pathnew = os.path.join(repopath(sock),pathnew)
    shutil.move(pathold,os.path.split(pathnew)[0])

def rename_file(sock,pathold,pathnew):
    #rename the file
    print "Received request to rename file"
    pathold = os.path.join(repopath(sock),pathold)
    pathnew = os.path.join(repopath(sock),pathnew)
    os.rename(pathold,pathnew)

#------- /HANDLE MOD REQUESTS ------------------


def listener(sock):
    """ Handles new connections to server """
    try:
        while True:
            print
            print "Waiting for a header..."
            TYPE, args = receive_header(sock)
            if not sock_email(sock) and TYPE != 1:
                #client has not authenticated yet, do nothing
                print "Client has not authenticated. Ignoring request", TYPE
                continue
            
            print "got header", TYPE, args, "from", sock
            handlers[TYPE](sock,*args)
            if TYPE in (2,4,5,6,7):
                socks = [pair[0] for pair in groups[sock_email(sock)] if pair[1] != sock] #get the other clients' watchers' sockets
                print "Forwarding to watcher(s) using", socks
                for othersock in socks:
                    relaybuffer[othersock].append([TYPE,args])
            print "dealt with it"
    except:
        traceback.print_exc()
        crash()
        
def receiver(sock):
    """ Receives stuff from the client, forwards it to either the watcher or the listener """
    while True:
        message = []
        byte = sock.recv(1)
        if byte in ('L','W'): #header
            while byte != chr(255):
                byte = sock.recv(1)
                message.append(byte)
        else: #raw data
            n = struct.unpack("H",sock.recv(2))[0]
            while len(message) < n:
                message.extend(list(sock.recv(n-len(message))))
            
        if byte in ('W','w'): #for watcher
            watchersockbuffer[sock].extend(list(message))
            if sock==debugsock: wrecv.extend(list(byte+struct.pack("H",n)[0])+message)
        else: #for listener
            listenersockbuffer[sock].extend(list(message))
            if sock==debugsock: lrecv.extend(list(byte+struct.pack("H",n)[0])+message)

handlers = {
        0:None, #special type; tells the listener do nothing and wait until the watcher frees up the socket before calling recv again
        1:authenticate, #no longer used as a request response
        2:make_folder,
        3:handle_send_request,
        4:receive_file,
        5:delete_file,
        6:move_file,
        7:rename_file
        }

groups = {} #groups of sockets that connect to clients using the same account, that need to be synchronized
relaybuffer = {}
socklock = {}
watchersockbuffer = {}
listenersockbuffer = {}
die = False
log = ""
wsend = []
wrecv = []
lsend = []
lrecv = []

clients = 0
if __name__ == "__main__":
	#setup database
	# dbc = db.init()
	# if not dbc[0]: raise dbc[1] # Couldn't connect with db

    # Setup port
    if server_config.ipv6:
        serversock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    else:
        serversock = socket.socket()
    serversock.bind(('localhost',7272)) # change back to config info
    serversock.listen(5)
    while clients < 2:
        clientsock, addr = serversock.accept()
        clients += 1
        if server_config.sslwrap:
            sock = ssl.wrap_socket(serversock, server_side=True, ssl_version=ssl.PROTOCOL_TLSv1)
        thread.start_new_thread(authenticate,(clientsock,))

    debugsock = clientsock
