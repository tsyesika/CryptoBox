#CryptoBox client
import socket, ssl, os, hashlib, easyaes, win32file, win32con, thread, traceback, time, common, client_config, shutil, struct, rpdb2
from common import makeheader, ceil


class _globals():
    pass

class Halfsock():
    """A wrapper class for socket that receives from a buffer list instead of the directly from socket.
    Also will not send until the socket is free, ensuring threads don't send at the same time."""
    def __init__(self,sock,_thread):
        self.sock = sock
        self._thread = _thread #1 = watcher, 2 = listener
    
    def recv(self,n):
        message = ""
        if self._thread == 1:
            Buffer = g.watchersockbuffer
        else:
            Buffer = g.listenersockbuffer
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
        while g.socklock:
            time.sleep(0.1)
        g.socklock = self._thread
        self.sock.send(recipient+struct.pack("H",len(message)))
        self.sock.send(message)
        g.socklock = 0
        if self._thread == 1:
            g.wsend.extend(list(recipient+struct.pack("H",len(message))+message))
        else:
            g.lsend.extend(list(recipient+struct.pack("H",len(message))+message))

def sha(x):
    return hashlib.sha512(x).digest()

def getrel(path):
    """Returns path relative to g.watchpath (with no leading slash)"""
    return path[len(g.watchpath)+1:]

def getabs(path):
    return g.watchpath + "\\" + path

def listdir_recursive(path):
    paths = [path]
    for entry in os.listdir(path):
        full = os.path.join(path,entry)
        if os.path.isdir(entry):
            paths.extend(listdir_recursive(full))
        else:
            paths.append(full)
    return paths

def getemailandpasshash():
    email = raw_input("Enter email: ")
    password = raw_input("Enter password: ")
    g.email = email
    g.password = password #this is hackish. Do not like.
    easyaes.initialize(email,password)
    passhash = sha(password)
    #pad email with 00000000 bytes for transmission; making it 64 bytes long
    email += chr(0)*(64-len(email))
    return email+passhash

def authenticate():
    message = getemailandpasshash()
    socket.send(message)

    reply = socket.recv(1)
    if ord(reply) == 1:
        print "Authentication successful"
        g.loggedin = True
    else:
        print "Authentication failed"

def receive_header(sock):
    header = ""
    while True:
        header += sock.recv(1)
        #print "header:", header
        if header == "#":
            thread.interrupt_main()
            raise
        if header[-1] == chr(255):
            #found end of header
            args = header.split(chr(0))[1:-1]
            #print "returning", header
            return ord(header[0]), args

def listener(sock):
    """ Listens for updates from the server """
    try:
        rpdb2.settrace()
        while True:
            print
            ##print "Listener is listening..."
            TYPE, args = receive_header(sock)
            ##print "got header", TYPE, args
            handlers[TYPE](sock,*args)
            ##print "dealt with it"
    except:
        traceback.print_exc()
        thread.interrupt_main()

def receiver(sock):
    """ Receives stuff from the client, forwards it to either the watcher or the listener """
    try:
        rpdb2.settrace()
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
                g.watchersockbuffer.extend(message)
                g.wrecv.extend(list(byte+struct.pack("H",n))+message)
            else: #for listener
                g.listenersockbuffer.extend(message)
                g.lrecv.extend(list(byte+struct.pack("H",n))+message)
    except:
        traceback.print_exc()
        thread.interrupt_main()

#---------------- SEND MOD REQUESTS -----------

def request_send(sock,path=None,exactsize=None):
    if not exactsize:
        print "Requesting to send", path
        length = ceil(os.stat(path).st_size,16)*16 + 256 #now length is a generous estimate of ciphertext filesize
        message = makeheader(3,length)
        sock.send(message) #send request has no body
    else:
        print "Requesting to send", exactsize, "bytes"
        sock.send(makeheader(3,exactsize))
    reply = sock.recv(1)
    if ord(reply) != 1:
        print "Upload request denied. Sorry."
        return False
    return True

def send_file(sock,path):
    cipher = []
    print "Encrypting..."
    easyaes.encrypt(path,cipher,g.password) #easyaes needs your password to make an IV)
    print "Done"
    cipher = "".join(cipher)
    
    exactlength = len(cipher)+ceil(len(cipher),256)*64
    #       length of file     +   number of hashes   *  64 bytes per hash
    # SEND HEAD
    message = makeheader(4,getrel(path),exactlength)
    sock.send(message)
    # SEND BODY
    r = upload(sock,cipher)
    print "File sent,", r, "blocks resent"

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
        print "resending block", i
        socket.send(
            makeheader(4, min(256,len(data)-i))
            )
        upload(data[ i : min(i+256,len(data)) ])
    return len(resend)

def remote_create(sock,path):
    if os.path.isfile(path):
        if request_send(sock,path):
            send_file(sock,path)
    else:
        #user made a folder
        message = makeheader(2,getrel(path))
        sock.send(message)

def remote_delete(sock,path):
    message = makeheader(5,getrel(path))
    sock.send(message)

def remote_move(sock,pathold,pathnew):
    message = makeheader(6,pathold,pathnew)
    sock.send(message)

def remote_rename(sock,pathold,pathnew):
    message = makeheader(7,pathold,pathnew)
    sock.send(message) 

#---------------- /SEND MOD REQUESTS ----------

def timer():
    oldlength = len(g.events)
    time.sleep(1)
    try:
        while len(g.events) > oldlength:
            oldlength = len(g.events)
            time.sleep(0.2) #this (hopefully) prevents a bug whereby an event that occurs exactly a seconds after another one can be chopped in half, creating two events, one of which normally confuses handleDirEvents
        if type(g.events) == tuple:
            print g.events
        g.queue.append(g.events)
        g.events = []
        g.timeline.append((time.clock(),"Collected"))
        handleDirEvents()
    except:
        traceback.print_exc()
        thread.interrupt_main()
    
def handleDirEvents():
    """Chew through events on the queue till there's none left"""
    print "HANDLE_DIR_EVENTS"
    events = g.queue.pop(0)
    print events
    summary = "".join([event[0] for event in events])
    print summary
    if [c for c in summary if c in "CDFT"]: #if there's anything that's not a U
        events = [event for event in events if event[0] != "U"] #get rid of Us
        summary = summary.replace("U","")
    print summary
    n = len(summary)
    if summary == "D"*n:
        #one or more files were deleted
        f, two = remote_delete, False
    elif summary == "C"*n:
        #one or more files were created
        f, two = remote_create, False
    elif summary == "U":
        #derp (always ignore these)
        print "HHHNNNNNNNGGGGGG"
        return
    elif summary == "UU":
        #a file was modified
        f, two = remote_create, False
        events = events[:1] #windows API returns two events per modification, so remove the second (I'm assuming only one file can be modified at once)
    elif summary == "DC"*(n/2):
        #one or more files were moved
        f, two = remote_move, True
    elif summary == "FT":
        #a file was renamed
        f, two = remote_rename, True
    else:
        print "Warning: unrecognised signature:"
        print events
        print summary
        f, two = lambda x,y:False, False
    #now actually process the event
    while events:
        a = events.pop(0)
        if two:
            b = events.pop(0)
            if not (a,b) in g.ignore:
                f(Halfsock(socket,1),getrel(a[1]),getrel(b[1]))
            else:
                g.ignore.remove((a,b))
                print "Ignored event pair", (a,b)
        else:
            if not a in g.ignore:
                f(Halfsock(socket,1),a[1])
            else:
                g.ignore.remove(a)
                print "Ignored event", a
    if g.queue:
        #the user's changed something in the directory while the last change
        #was being processed
        print g.queue
        handleDirEvents()
                    

def watcher():
    try:
        rpdb2.settrace()
        #print "watcher invoked"
        #Thanks to Tim Golden for most of this code: http://timgolden.me.uk/python/win32_how_do_i/watch_directory_for_changes.html
        ACTIONS = {
        1 : "C",  #CREATED
        2 : "D",  #DELETED
        3 : "U",  #UPDATED
        4 : "F",  #RENAMED FROM
        5 : "T"   #RENAMED TO
        }
        
        FILE_LIST_DIRECTORY = 0x0001

        path_to_watch = g.watchpath
        hDir = win32file.CreateFile (
        path_to_watch,
        FILE_LIST_DIRECTORY,
        win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
        None,
        win32con.OPEN_EXISTING,
        win32con.FILE_FLAG_BACKUP_SEMANTICS,
        None
        )
        while True:
            #
            # ReadDirectoryChangesW takes a previously-created
            #  handle to a directory, a buffer size for results,
            #  a flag to indicate whether to watch subtrees and
            #  a filter of what changes to notify.
            results = win32file.ReadDirectoryChangesW (
            hDir,
            2048,
            True,
            win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
            win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
            win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
            win32con.FILE_NOTIFY_CHANGE_SIZE |
            win32con.FILE_NOTIFY_CHANGE_LAST_WRITE |
            win32con.FILE_NOTIFY_CHANGE_SECURITY,
            None,
            None
            )
            results = [(ACTIONS[action],os.path.join(g.watchpath,str(path))) for action, path in results]
            #                                                     ^ (paths are in unicode by default)
            g.timeline.append((time.clock(),results))
            #print "tick"
            if not g.events:
                thread.start_new_thread(timer,())
            g.events.extend(results)
    except:
        traceback.print_exc()
        thread.interrupt_main()

def crash():
    socket.send("#")

#------- HANDLE MOD REQUESTS ------------------

def make_folder(sock,path):
    #print "Received request to make folder", path
    path = getabs(path)
    g.ignore.append(("C",path))
    os.mkdir(path)

def handle_send_request(sock,filesize):
    #print "Received space check request for", filesize, "bytes"
    filesize = int(filesize)
    sock.send(chr(1),'w') #for now we'll just say yes

def receive_file(sock,path,exactsize):
    #make sure the watcher doesn't spot this change and report it to the server
    #this must be done by predicting exactly what event will be generated when the modification is made and warning handleDirEvents to ignore it
    path = os.path.join(g.watchpath,path)
    if os.path.exists(path):
        g.ignore.append(("U",path)) #a file's actually being modified, not created
    else:
        g.ignore.append(("C",path))
    filebinary = download(sock,exactsize)
    filebinary = easyaes.decrypt(filebinary,path,g.password)

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
        ##print "got block", len(block), len(HASH)
        #check block
        if sha(block) != HASH:
            #add a resend request
            #print "hash doesn't match"
            resend.append(bytesreceived - 64*bytesreceived / 320) #working out where the corrupted block started in the original data (without hashes)
        bytestream += block #don't worry, we'll request a resend and overwrite it if it was corrupted
        bytesreceived += 256+64
    #print len(resend), "out of", ceil(exactsize,256), "blocks corrupted"
    message = ""
    for i in resend: #i for index (in the original, unhashed bytestream back on clientside)
        raise
        message += str(i) + chr(0)
    message += chr(255)
    sock.send(message,'w')
    #print "sent acknowledgement:", message
    for i in resend:
        #now receive the resends, if any
        #print "getting resend", i
        exactsize = receive_header(sock)[1][0]
        block = download(sock,exactsize)
        #print "got resend"
        #now insert the correct block back into the bytestream, overwriting the corrupted block
        bytestream = bytestream[:i]+block+bytestream[i+256:]
    return bytestream

def delete_file(sock,path):
    #print "Received request to delete file", path
    path = os.path.join(g.watchpath,path)
    if os.path.isdir(path):
        g.ignore.extend(
            [("D",killpath) for killpath in listdir_recursive(path)]
            )
        shutil.rmtree(path)
    else:
        g.ignore.append(("D",path))
        os.remove(path)
    

def move_file(sock,pathold,pathnew):
    #move the file
    #print "Received request to move file"
    pathold = os.path.join(g.watchpath,pathold)
    pathnew = os.path.join(g.watchpath,pathnew)
    g.ignore.append( (("D",pathold),("C",pathnew)) )
    shutil.move(pathold,os.path.split(pathnew)[0])

def rename_file(sock,pathold,pathnew):
    #rename the file
    #print "Received request to rename file"
    pathold = os.path.join(g.watchpath,pathold)
    pathnew = os.path.join(g.watchpath,pathnew)
    g.ignore.append( (("F",pathold),("T",pathnew)) )
    os.rename(pathold,pathnew)

#------- /HANDLE MOD REQUESTS ------------------

handlers = {
        1:None,
        2:make_folder,
        3:handle_send_request,
        4:receive_file,
        5:delete_file,
        6:move_file,
        7:rename_file
        }

if __name__ == "__main__":
    #message header 1st bytes:
    #1 - Deprecated
    #2 - new account request (Deprecated. The number 2 will be reassigned later)
    #3 - send request (followed by approximate file size)
    #4 - incoming file (next four bytes store number of 16-byte blocks in file as an integer)
    #5 - delete file
    #6 - move file
    #7 - rename file
    g = _globals()
    g.loggedin = False
    g.events = []
    g.resettimer = False
    g.watchpath = client_config.watchpath
    g.queue = []
    g.socklock = 0 #0 = no lock, 1 = locked to watcher, 2 = locked to listener
    g.watchersockbuffer = []
    g.listenersockbuffer = []
    g.ignore = []
    g.timeline = []
    g.wsend = []
    g.wrecv = []
    g.lsend = []
    g.lrecv = []
    time.clock()

    socket = socket.socket()
    print "Connecting..."
    socket.connect(('localhost',7272))
    print "Connected"
    
    authenticate()
    if raw_input("Watch folder 2? "): g.watchpath = r"C:\Users\Philip\Desktop\cryptobox2"
    thread.start_new_thread(watcher,())
    thread.start_new_thread(listener,(Halfsock(socket,2),) )
    thread.start_new_thread(receiver,(socket,) )
