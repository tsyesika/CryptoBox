#transfer.py
#a module providing file transfer routines for both client and server
import easyaes, time, hashlib, os, thread
from math import ceil as __ceil__

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
    header = chr(first) + chr(0)*bool(args)
    for arg in args:
        if type(arg) == str:
            header += arg + chr(0)
        elif type(arg) == int or type(arg) == float:
            header += str(arg) + chr(0)
        else:
            raise Exception("Unsupported type (can only send strings, ints and floats")
    header += chr(255) #i'd really prefer to use something like : and | as delimiters, but since there doesn't seem to be a single character that doesn't appear in file paths on any system, I'm using non-printable characters
    return header

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
            print resend
            resend = [int(i) for i in resend.split(chr(0))[:-1]]
            break
    print "resend =", resend
    for i in resend:
        #resend corrupted blocks
        print "resending block", i
        socket.send(
            makeheader(4, min(256,len(data)-i))
            )
        upload(data[ i : min(i+256,len(data)) ])
    return len(resend)
