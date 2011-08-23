##
# Server App
# Version 0.1
# Developed by Jessica T. & Philip J.
##

import socket, os, hashlib, thread, server_config, ssl, time, common, traceback, shutil
from common import makeheader

# if config.database_type == "mysql":
#	import db.mysql as db
# elif config.database_type == "sqlite":
#	import db.sqlite as db
# elif config.database_type == "pickle":
#	import db.pickle as db
# else:
# 	raise # some kinda error as no database has been selected?

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
        if email in groups:
            #one or more clients of this account are already logged in
            groups[email].add(sock)
        else:
            groups[email] = set([sock])
        print groups
        relaybuffer[sock] = []
        socklock[sock] = 0 #0 = no lock, 1 = locked to watcher, 2 = locked to listener
        sock.send(chr(1)) #YES MR TEST I CAN SEE FROM MY DATABASE THAT YOU DO INDEED OWN THIS ACCOUNT HERE HAVE SOME FILES
        thread.start_new_thread(watcher,(sock,))
        listener(sock)
    except:
        traceback.print_exc()
        thread.interrupt_main()

def receive_header(sock):
    header = ""
    while True:
        header += sock.recv(1)
        if header == "#":
            print "HERP FUCKING DERP"
            global die
            die = True
            sock.close()
            serversock.close()
            thread.interrupt_main()
            raise Exception("HERP FUCKING DERP")
        if socklock[sock] == 1: #watcher's got the socket
            common.g.watchersockbuffer.append(header)
            header = ""
            continue
        if header[-1] == chr(255):
            #found end of header
            args = header.split(chr(0))[1:-1]
            return ord(header[0]), args

def sock_email(sock):
    """Returns the email address of the user of the client that sock is connected to"""
    for email in groups:
        if sock in groups[email]:
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
            if relaybuffer[sock] and not socklock[sock]:
                socklock[sock] = 1
                while relaybuffer[sock]:
                    message = relaybuffer[sock].pop(0)
                    relay(sock,message[0],message[1])
                socklock[sock] = 0
    except:
        traceback.print_exc()
        crash()

#---------------- SEND MOD REQUESTS -----------

def relay(sock,command,args):
    if command == 4:
        #a file was added to a folder; now add it to yours
        common.socket = common.WatcherSock(sock)
        if common.request_send(exactsize=int(args[1])+256):
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

def send_file(sock,path):
    fin = open(repopath(sock)+"\\"+path,"rb")
    data = fin.read()
    exactlength = len(data)+common.ceil(len(data),256)*64
    #       length of file    + number of hashes   *  64 bytes per hash
    # SEND HEAD
    message = makeheader(4,path,exactlength)
    sock.send(message)
    # SEND BODY
    r = common.upload(data)
    print "File sent,", r, "blocks resent"

#---------------- /SEND MOD REQUESTS ----------



#------- HANDLE MOD REQUESTS ------------------

def receive_file(sock,path,exactsize):
    filebinary = common.download(sock,exactsize)
    fout = open(repopath(sock)+"\\"+path,"wb")
    fout.write(filebinary)
    fout.close()

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
    pathold = os.path.join(repopath(sock),pathold)
    pathnew = os.path.join(repopath(sock),pathnew)
    shutil.move(pathold,os.path.split(pathnew)[0])

def rename_file(sock,pathold,pathnew):
    #rename the file
    global log
    pathold = os.path.join(repopath(sock),pathold)
    pathnew = os.path.join(repopath(sock),pathnew)
    log = (pathold, pathnew)
    if not os.path.exists(pathold):
        raise
    else:
        os.rename(pathold,pathnew)

#------- /HANDLE MOD REQUESTS ------------------


def listener(sock):
    """ Handles new connections to server """
    while True:
        print
        print "Waiting for a header..."
        TYPE, args = receive_header(sock)
        if not sock_email(sock) and TYPE != 1:
            #client has not authenticated yet, do nothing
            print "Client has not authenticated. Ignoring request", TYPE
            continue
        
        socklock[sock] = 2 #make sure the watcher doesn't interupt in
        print "got header", TYPE, args, "from", sock
        handlers[TYPE](sock,*args)
        if TYPE in (4,5,6,7):
            socks = set(groups[sock_email(sock)])
            print socks
            socks.remove(sock)
            print socks
            for othersock in socks:
                relaybuffer[othersock].append([TYPE,args])
        socklock[sock] = 0 #free up the socket
        print "dealt with it"
        

handlers = {
        0:None, #special type; tells the listener do nothing and wait until the watcher frees up the socket before calling recv again
        1:authenticate, #no longer used as a request response
        2:None, #ignore this
        3:common.handle_send_request,
        4:receive_file,
        5:delete_file,
        6:move_file,
        7:rename_file
        }

groups = {} #groups of sockets that connect to clients using the same account, that need to be synchronized
relaybuffer = {}
socklock = {}
die = False
log = ""

clients = 0
if __name__ == "__main__":
	#setup database
	# dbc = db.init()
	# if not dbc[0]: raise dbc[1] # Couldn't connect with db
    while clients < 2:
        # Setup port
        if server_config.ipv6:
            serversock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        else:
            serversock = socket.socket()
        serversock.bind(('localhost',7274)) # change back to config info
        serversock.listen(5)
        
        clientsock, addr = serversock.accept()
        clients += 1
        if server_config.sslwrap:
            sock = ssl.wrap_socket(serversock, server_side=True, ssl_version=ssl.PROTOCOL_TLSv1)
        thread.start_new_thread(authenticate,(clientsock,))
