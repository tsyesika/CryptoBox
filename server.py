##
# Server App
# Version 0.1
# Developed by Jessica T. & Philip J.
##

import socket, hashlib, thread, server_config, ssl

def Connection_Handler(sock):
	""" Handles new connections to server """
	ID = sock.recv(128) #receive email and password hash from client
	email = ID[:64]
	email = email[email.index(chr(0))] #shave off the padding
	passhash = ID[:64]
	

if __name__ == "__main__":
	# Setup port
	if server_config.ipv6:
		sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
	else:
		sock = socket.socket()
		sock.bind(config.bind_ip,config.bind_port)
	while True:
		sock, addr = sock.accept()
		if server_config.sslwrap:
			sock = ssl.wrap_socket(sock, server_side=True, ssl_version=ssl.PROTOCOL_TLSv1)
		thread.start_new_thread(Connection_Handler, (sock,))
