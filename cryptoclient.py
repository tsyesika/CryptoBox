#CryptoBox client
import socket, ssl, os, hashlib, easyaes, win32file, win32con, thread, traceback, time, common, client_config, shutil
from common import makeheader

class _globals():
    def __setattr__(self,name,value):
        self.__dict__[name] = value
        common.g.__dict__[name] = value #functions both in cryptoclient's namespace and in common's need access to g, so it's important to synchronize them

def sha(x):
    return hashlib.sha512(x).digest()

def getrel(path):
    """Returns path relative to g.watchpath (with no leading slash"""
    return path[len(g.watchpath)+1:]

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
        if g.socklock == 1: #watcher's got the socket
                g.watchersockbuffer.append(header)
                header = ""
                continue
        if header == "#":
            thread.interrupt_main()
            raise
        if header[-1] == chr(255):
            #found end of header
            args = header.split(chr(0))[1:-1]
            return ord(header[0]), args

def listener():
    """ Listens for updates from the server """
    try:
        while True:
            print
            print "Listener is listening..."
            TYPE, args = receive_header(socket)
            g.socklock = 2 #make sure the watcher doesn't interupt in
            print "got header", TYPE, args
            handlers[TYPE](socket,*args)
            g.socklock = 0 #free up the socket
            print "g.ignore =", g.ignore
            print "dealt with it"
    except:
        traceback.print_exc()
        thread.interrupt_main()

#---------------- SEND MOD REQUESTS -----------

def send_file(path):
    cipher = []
    print "Encrypting..."
    easyaes.encrypt(g.watchpath+"\\"+path,cipher,g.password) #easyaes needs your password to make an IV)
    print "Done"
    cipher = "".join(cipher)
    
    exactlength = len(cipher)+common.ceil(len(cipher),256)*64
    #       length of file     +   number of hashes   *  64 bytes per hash
    # SEND HEAD
    message = makeheader(4,path,exactlength)
    socket.send(message)
    # SEND BODY
    r = common.upload(cipher)
    print "File sent,", r, "blocks resent"

def remote_create(path):
    if common.request_send(g.watchpath+"\\"+path):
        send_file(path)

def remote_delete(path):
    message = makeheader(5,path)
    socket.send(message)

def remote_move(pathold,pathnew):
    message = makeheader(6,pathold,pathnew)
    socket.send(message)

def remote_rename(pathold,pathnew):
    message = makeheader(7,pathold,pathnew)
    socket.send(message) 

#---------------- /SEND MOD REQUESTS ----------

def timer():
    time.sleep(1)
    try:
        g.queue.append(g.events)
        g.events = []
        while g.socklock == 2:
            time.sleep(0.5) #wait till the listener finishes with the socket
        if g.socklock == 0: #don't start processing them if another thread already has (in which case g.socklock == 1)
            g.socklock = 1
            handleDirEvents()
            g.socklock = 0
    except:
        traceback.print_exc()
        thread.interrupt_main()
    
def handleDirEvents():
    """Chew through events on the queue till there's none left"""
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
    elif summary[0] == "U":
        #a file was modified
        remote_create(events[0][1])
        return
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
    #now actually process the event
    while events:
        a = events.pop(0)
        if two:
            b = event = events.pop(0)
            if not (a,b) in g.ignore:
                f(getrel(a[1]),getrel(b[1]))
            else:
                g.ignore.remove((a,b))
        else:
            if not a in g.ignore:
                f(getrel(a[1])) #chop off the start so it just sends the path relative to watchpath (with no leading slash)
            else:
                g.ignore.remove(a)
    if g.queue:
        #the user's changed something in the directory while the last change
        #was being processed
        handleDirEvents()
                    

def watcher():
    print "watcher invoked"
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
        print "tick"
        if not g.events:
            thread.start_new_thread(timer,())
        g.events.extend(results)

def crash():
    socket.send("#")

#------- HANDLE MOD REQUESTS ------------------

def handle_send_request(sock,filesize):
    filesize = int(filesize)
    sock.send(chr(1)) #for now we'll just say yes

def receive_file(sock,path,exactsize):
    #make sure the watcher doesn't spot this change and report it to the server
    path = os.path.join(g.watchpath,path)
    g.ignore.append(("C",path)) #this must be done by predicting exactly what event will be generated when the modification is made and warning handleDirEvents to ignore it
    filebinary = common.download(sock,exactsize)
    filebinary = easyaes.decrypt(filebinary,path,g.password)

def delete_file(sock,path):
    path = os.path.join(g.watchpath,path)
    g.ignore.append(("D",path))
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)
    print "Received request to delete file", path

def move_file(sock,pathold,pathnew):
    #move the file
    pathold = os.path.join(g.watchpath,pathold)
    pathnew = os.path.join(g.watchpath,pathnew)
    shutil.move(pathold,os.path.split(pathnew)[0])

def rename_file(sock,pathold,pathnew):
    #rename the file
    pathold = os.path.join(g.watchpath,pathold)
    pathnew = os.path.join(g.watchpath,pathnew)
    g.ignore.append( (("F",pathold),("T",pathnew)) )
    os.rename(pathold,pathnew)

#------- /HANDLE MOD REQUESTS ------------------

handlers = {
        1:None,
        2:None,
        3:handle_send_request,
        4:receive_file,
        5:delete_file,
        6:move_file,
        7:rename_file
        }

if __name__ == "__main__":
    #message header 1st bytes:
    #1 - authentication request
    #2 - new account request (Deprecated. The number 2 will be reassigned later)
    #3 - send request (followed by approximate file size)
    #4 - incoming file (next four bytes store number of 16-byte blocks in file as an integer)
    #5 - delete file
    g = _globals()
    g.loggedin = False
    g.events = []
    g.resettimer = False
    g.watchpath = client_config.watchpath
    g.queue = []
    g.socklock = 0 #0 = no lock, 1 = locked to watcher, 2 = locked to listener
    g.watchersockbuffer = []
    g.ignore = []

    socket = socket.socket()
    print "Connecting..."
    socket.connect(('localhost',7274))
    print "Connected"

    common.socket = common.WatcherSock(socket) #all common functions used by watcher use the global variable socket; all used by listener will take the normal socket as an argument

    authenticate()
    if raw_input("Watch folder 2? "): g.watchpath = r"C:\Users\Philip\Desktop\cryptobox2"
    thread.start_new_thread(listener,())
    watcher()
