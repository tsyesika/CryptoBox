import os, hashlib, struct
from aespython import key_expander, aes_cipher, cbc_mode

def getfileobject(path,writemode):
    if type(path) == file:
        return path
    pathsplit = os.path.split(path)
    if not os.path.exists(pathsplit[0]) or not (os.path.exists(path) or writemode):
        raise Exception("Invalid path %s" % path)
    if not os.path.exists(path): #invalid path tail
        print "Creating new file for writing called", path
        return open(path,"wb")
    if writemode:
        return open(path,"wb")
    else:
        return open(path,"rb")

def sha(x):
    return hashlib.sha512(x).digest()

def initialize(email,password):
    global aes_cbc_256
    key = bytearray(sha(email+password)[:32])
    #using AES-256, CBC mode
    key_expander_256 = key_expander.KeyExpander(256) #(256 bit key)
    expanded_key = key_expander_256.expand(key) #produces a longer, usable key
    aes_cipher_256 = aes_cipher.AESCipher(expanded_key)
    aes_cbc_256 = cbc_mode.CBCMode(aes_cipher_256, 16) #16 bits = block size

def encrypt(plaintext,out,password):
    #takes a file plaintext
    #outputs ciphertext to either a file or a list
    plaintext = getfileobject(plaintext,False)
    plaintext.seek(0,os.SEEK_END)
    length = plaintext.tell() #get file length, so the decrypter knows how many bytes padding to ignore
    plaintext.seek(0) #put the cursor back to the start of the file

    outtolist = False
    if isinstance(out,list):
        out.append(struct.pack("L",length))
        outtolist = True
    elif isinstance(out,str) or isinstance(out,file):
        out = getfileobject(out,True)
        out.write(struct.pack("L",length))
    else:
        #out is not a list, file or path
        raise TypeError("out must be a list, file or path string")    

    #CREATE AN IV AND STORE ITS KEY FOR GENERATION WHEN IT'S DECRYPTION TIME
    ivkey = os.urandom(16)
    iv = sha(ivkey+password)
    h = sha(plaintext.read())
    plaintext.seek(0)
    fout = open("iv_table.txt","a")
    fout.write(h+":"+ivkey+"\n") #store the ivkey for decrypting the file later
    fout.close()
    
    aes_cbc_256.set_iv(iv)
    while True:
        plainblock = bytearray(plaintext.read(16)) #16-byte blocks
        if len(plainblock) == 0:
            #PKCS7 padding was applied automatically to the previous block
            break
        cipherblock = aes_cbc_256.encrypt_block(plainblock)
        cipherblock = "".join([chr(i) for i in cipherblock])
        if outtolist:
            out.append(cipherblock)
        else:
            out.write(cipherblock)
    if not outtolist:
        out.close()

def decrypt(ciphertext,out,iv):
    #takes a file, path string or list ciphertext
    #creates a plaintext file out, which must be a file object or path string
    readfromfile = False
    if type(ciphertext) in (file,str):
        readfromfile = True
        ciphertext = getfileobject(ciphertext,False)
        length = ciphertext.read(struct.calcsize("L"))
        length = struct.unpack("L",length)[0]
    elif type(ciphertext) == list:
        length = struct.unpack("L",ciphertext[0])[0]
        del ciphertext[0]
    else:
        #ciphertext is not a list, file or path
        raise TypeError("ciphertext must be a list, file or path string")
    out = getfileobject(out,True)
    
    blocks = 0
    plainblock = ""
    aes_cbc_256.set_iv(iv)
    while True:
        if readfromfile:
            cipherblock = list(bytearray(ciphertext.read(16))) #16-byte (128 bit) blocks
        else:
            if ciphertext:
                cipherblock = [ord(char) for char in ciphertext.pop(0)]
            else:
                cipherblock = []
        if len(cipherblock) == 0:
            #EOF
            padding = blocks*16 - length
            out.write(plainblock[:16-padding])
            break
        else:
            out.write(plainblock)
        blocks += 1
        plainblock = aes_cbc_256.decrypt_block(cipherblock)
        plainblock = "".join([chr(i) for i in plainblock])
        
    out.close()
    if readfromfile:
        ciphertext.close()


aes_cbc_256 = None
