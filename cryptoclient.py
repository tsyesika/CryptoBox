#CryptoBox client
import socket, ssl, os, hashlib, struct
from aespython import key_expander, aes_cipher, cbc_mode


def encrypt(plaintext,out):
    #takes a file plaintext
    #outputs ciphertext to either a file or a list
    plaintext.seek(0,os.SEEK_END)
    length = plaintext.tell() #get file length, so the decrypter knows how many bytes padding to ignore
    plaintext.seek(0) #put the cursor back to the start of the file

    outtolist = False
    if isinstance(out,list):
        out.append(struct.pack("L",length))
        outtolist = True
    elif isinstance(out,str):
        pathsplit = os.path.split(out)
        if not os.path.exists(pathsplit[0]):
            raise Exception("Invalid path %s" % out)
        if not os.path.exists(pathsplit[1]):
            print "Creating new cipher file", out
        out = open(out,"wb")
        out.write(struct.pack("L",length))
    elif isinstance(out,file):
        out.write(struct.pack("L",length))
    else:
        #out is not a list, file or path
        raise TypeError("out must be a list, file or path string")    
    
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

def decrypt(ciphertext):
    #takes a file ciphertext
    #creates a plaintext file, currently called decrypted.txt
    fout = open("decrypted.txt","wb")
    aes_cbc_256.set_iv(iv) #reset the iv to prevent the first block being b0rk'd
    length = ciphertext.read(struct.calcsize("L"))
    length = struct.unpack("L",length)[0]
    blocks = 0
    out = ""
    plainblock = ""
    while True:
        cipherblock = list(bytearray(ciphertext.read(16))) #16-byte (128 bit) blocks
        if len(cipherblock) == 0:
            #EOF
            padding = blocks*16 - length
            fout.write(plainblock[:16-padding])
            break
        else:
            fout.write(plainblock)
        blocks += 1
        plainblock = aes_cbc_256.decrypt_block(cipherblock)
        plainblock = "".join([chr(i) for i in plainblock])
        
    fout.close()
    ciphertext.close()

plaintext = open(r"C:\Users\Philip\python\cryptobox\testfile.txt","rb")
salt = '\xe1(\xfe\xfb\xba\xad\xd4\x8c\xb8ZZ\x86\x08\xc9\x1c\x95>\xa3\xb3\xc0pr\r\xc2\x9c[\xa7>\xfa\x0c\xc8\xc6'
key = bytearray(hashlib.sha512("password"+salt).digest()[:32])
iv = bytearray(hashlib.sha512("password").digest()[:16])

#using AES-256, CBC mode
key_expander_256 = key_expander.KeyExpander(256) #(256 bit key)
expanded_key = key_expander_256.expand(key) #produces a longer, usable key
aes_cipher_256 = aes_cipher.AESCipher(expanded_key)
aes_cbc_256 = cbc_mode.CBCMode(aes_cipher_256, 16) #16 bits = block size
aes_cbc_256.set_iv(iv)

#outfile = open(r"C:\Users\Philip\python\cryptobox\cipher.txt","wb")
outpath = r"C:\Users\Philip\python\cryptobox\cipher.txt"
#outlist = []
encrypt(plaintext,outlist)
ciphertext = open(r"C:\Users\Philip\python\cryptobox\cipher.txt","rb")
decrypt(ciphertext)
ciphertext.close()
