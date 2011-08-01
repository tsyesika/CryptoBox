#CryptoBox client

# Is this a windows only client?
import socket, ssl, os, hashlib, struct, easyaes, win32file, win32con, thread, traceback, time
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

def request_send(path):
    length = ceil(os.stat(path).st_size,16) #now length is number of blocks
    message = makeheader(3,struct.pack("i",length+1)) #add a block to length, just to be safe
    socket.send(message) #send request has no body
    reply = socket.recv(1)
    if ord(reply) != 1:
        print "Upload request denied. Sorry."
        return False
    return True

def send_file(path):
    cipher = []
    easyaes.encrypt(path,cipher,g.password) #easyaes needs your password to make an IV)
    cipher = "".join(cipher)
    
    exactlength = len(cipher)+ceil(len(cipher),256)*64
    #       length of file    + number of hashes   *  64 bytes per hash
    message = makeheader(4,path,struct.pack("i",exactlength))
    socket.send(message)
    r = upload(cipher)
    print "File sent,", r, "blocks resent"
    
def upload(data):
    """ Sends a large string data to the server, using sha to ensure integrity """
    # SEND HEAD
    
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

def download(exactsize):
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

def remote_delete(path):
    message = makeheader(5,path)
    socket.send(message)

def remote_create(path):
    if request_send(path):
        send_file(path)

def remote_move(pathold,pathnew):
    message = makeheader(6,pathold,pathnew)
    socket.send(message)

def remote_rename(pathold,pathnew):
    message = makeheader(7,pathold,pathnew)
    socket.send(message)

def timer():
    time.sleep(1)
    try:
        handleDirEvent()
    except:
        traceback.print_exc()
    
def handleDirEvent():
    events = g.events
    g.events = []
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
    while events:
        a = events.pop(0)
        if two:
            b = event = events.pop(0)
            f(a[1],b[1])
        else:
            f(a[1])
                    

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
        #                                                 ^ (paths are in unicode by default)
        print "tick"
        if results:
            try:
                if results[0][0] == "F": #renamed file
                    crash()
            except:
                print results
                raise
        if not g.events:
            thread.start_new_thread(timer,())
        else:
            g.resettimer = True  #keep resetting the timer when more events come through, to make sure handleDirEvent gets all of them
        g.events.extend(results)

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

	socket = socket.socket()
	print "Connecting..."
	socket.connect(('localhost',7282))
	print "Connected"

	authenticate()

	def crash():
	    socket.send("#")
