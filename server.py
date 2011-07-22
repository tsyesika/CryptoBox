##
# Server App
# Version 0.1
# Developed by Jessica T. & Philip J.
##

import socket, hashlib, thread, server_config, ssl

def sha(x):
    return hashlib.sha512(x).digest()

def authenticate(sock):
        ID = sock.recv(128) #receive email and password hash from client
        email = ID[:64]
        email = email[email.index(chr(0))] #shave off the padding
        passhash = ID[:64]
        #now check against the database

def new_account(sock):
        ID = sock.recv(128) #receive email and password hash from client
        email = ID[:64]
        email = email[email.index(chr(0))] #shave off the padding
        passhash = ID[:64]
        salt = os.urandom(32)
        storepass = sha(salt+passhash)
        #now put it in a database or something
        sock.send(chr(1)) #signal a successful account creation

def Connection_Handler(sock):
	""" Handles new connections to server """
	header = ""
	while True:
                header += sock.recv(1)
                if header[-1] == "|":
                        #found end of header
                        args = header.split(":")[1:-1]
                        handler = ord(header[0])
                        handlers[handler](sock,*args)
                
handlers = {
        1:authenticate
        2:new_account
        }

if __name__ == "__main__":
	# Setup port
	if server_config.ipv6:
		sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
	else:
		sock = socket.socket()
		sock.bind(config.bind_ip,config.bind_port)
		sock.listen(5)
	while True:
		sock, addr = sock.accept()
		if server_config.sslwrap:
			sock = ssl.wrap_socket(sock, server_side=True, ssl_version=ssl.PROTOCOL_TLSv1)
		thread.start_new_thread(Connection_Handler, (sock,))
