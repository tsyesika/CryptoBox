#CryptoBox client
import socket, ssl, os, hashlib, easyaes, win32file, win32con, thread, traceback, time, common
from common import makeheader

class _globals():
    def __setattr__(self,name,value):
        self.__dict__[name] = value
        common.g.__dict__[name] = value #functions both in cryptoclient's namespace and in common's need access to g, so it's important to synchronize them

def sha(x):
    return hashlib.sha512(x).digest()

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

def remote_delete(path):
    message = makeheader(5,path)
    socket.send(message)

def remote_create(path):
    if common.request_send(path):
        common.send_file(path)

def remote_move(pathold,pathnew):
    message = makeheader(6,pathold,pathnew)
    socket.send(message)

def remote_rename(pathold,pathnew):
    message = makeheader(7,pathold,pathnew)
    socket.send(message)

def timer():
    time.sleep(1)
    try:
        g.queue.append(g.events)
        g.events = []
        if not g.processing:
            g.processing = True
            handleDirEvent()
            g.processing = False
    except:
        traceback.print_exc()
    
def handleDirEvent():
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
            f(a[1],b[1])
        else:
            f(a[1])
    if g.queue:
        #the user's changed something in the directory while the last change
        #was being processed
        handleDirEvent()
                    

def dirwatch():
    #Thanks to Tim Golden for most of this code: http://timgolden.me.uk/python/win32_how_do_i/watch_directory_for_changes.html
    ACTIONS = {
    1 : "C",  #CREATED
    2 : "D",  #DELETED
    3 : "U",  #UPDATED
    4 : "F",  #RENAMED FROM
    5 : "T"   #RENAMED TO
    }
    
    FILE_LIST_DIRECTORY = 0x0001

    path_to_watch = "."
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
        results = [(ACTIONS[action],os.path.join(g.rootdir,str(path))) for action, path in results]
        #                                                   ^ (paths are in unicode by default)
        print "tick"
        if results:
            if results[0][0] == "F": #renamed file
                crash()
        if not g.events:
            thread.start_new_thread(timer,())
        g.events.extend(results)

def crash():
	socket.send("#")

if __name__ == "__main__":
	#message header 1st bytes:
	#1 - authentication request
	#2 - new account request (Remove?)
	#3 - send request (followed by approximate file size)
	#4 - incoming file (next four bytes store number of 16-byte blocks in file as an integer)
	#5 - delete file
	g = _globals()
	g.loggedin = False
	g.events = []
	g.resettimer = False
	g.rootdir = "C:\Users\Philip\python\cryptobox"
	g.queue = []
	g.processing = False

	socket = socket.socket()
	print "Connecting..."
	socket.connect(('localhost',7274))
	print "Connected"
	common.socket = socket #give common functions access to the socket

	authenticate()
	dirwatch()
