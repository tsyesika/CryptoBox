##
# Server App
# Version 0.1
# Developed by Jessica T. & Philip J.
##

import socket, hashlib, thread, server_config, ssl

def Connection_Handler(sock):
	""" Handles new connections to server """
	pass
	

if __name__ == "__main__":
	# Setup port
	if server_config.ipv6:
		sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
	else:
		sock = socket.socket()
	while True:
		sock, addr = sock.accept()
		if server_config.sslwrap:
			sock = ssl.wrap_socket(sock, server_side=True, ssl_version=ssl.PROTOCOL_TLSv1)
		thread.start_new_thread(Connection_Handler, (sock,))