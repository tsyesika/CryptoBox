##
# Server App
# Version 0.1
# Developed by Jessica T. & Philip J.
##

import socket, os, hashlib, thread, server_config, ssl, time, common


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


def authenticate(sock):
        ID = sock.recv(128) #receive email and password hash from client
        email = ID[:64]
        email = email[email.index(chr(0))] #shave off the padding
        passhash = ID[:64]
		
		# salt = db.getsalt(dbc, email)
		# if salt[0]: salt = salt[0]
		# else: #incorrect :(

        passhash = sha(passhash) # + salt?
		#now check against the database

		# res = db.login(dbc, email, pass)
		# if res[0]:
			# Correct
		# else:
			# Incorrect
		
        sock.send(chr(1)) #YES MR TEST I CAN SEE FROM MY DATABASE THAT YOU DO INDEED OWN THIS ACCOUNT HERE HAVE SOME FILES

def new_account(sock):
		
		# Is this needed?
	
        ID = sock.recv(128) #receive email and password hash from client
        email = ID[:64]
        email = email[email.index(chr(0))] #shave off the padding
        passhash = ID[:64]
        salt = os.urandom(32)
        storepass = sha(salt+passhash)
        #now put it in a database or something
        sock.send(chr(1)) #signal a successful account creation


def receive_header(sock):
    header = ""
    while True:
        header += sock.recv(1)
        if header == "#":
                raise
        if header[-1] == chr(255):
            #found end of header
            args = header.split(chr(0))[1:-1]
            return ord(header[0]), args

def Connection_Handler(sock):
    """ Handles new connections to server """
    while True:
        print
        print "Waiting for a header..."
        TYPE, args = receive_header(sock)
        print "got header", TYPE, args
        handlers[TYPE](sock,*args)
        print "dealt with it"

handlers = {
        1:authenticate,
        2:new_account,
        3:common.handle_send_request,
        4:common.receive_file,
        5:common.delete_file,
        6:common.move_file,
        7:common.rename_file
        }

if __name__ == "__main__":
	#setup database
	# dbc = db.init()
	# if not dbc[0]: raise dbc[1] # Couldn't connect with db
	
    # Setup port
    if server_config.ipv6:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    else:
        sock = socket.socket()
    sock.bind(('localhost',7274)) # change back to config info
    sock.listen(5)
    while True:
        print sock
        clientsock, addr = sock.accept()
        if server_config.sslwrap:
            sock = ssl.wrap_socket(sock, server_side=True, ssl_version=ssl.PROTOCOL_TLSv1)
        Connection_Handler(clientsock)
        #thread.start_new_thread(Connection_Handler, (clientsock,))
