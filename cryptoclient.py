#CryptoBox client
import socket, ssl, os, hashlib, struct
from aespython import key_expander, aes_cipher, cbc_mode


def encrypt(plaintext):
    #takes a file plaintext
    #creates a ciphertext file, currently called cipher.txt
    fout = open("cipher.txt","wb")
    length = os.stat(r"C:\Users\Philip\python\cryptobox\testfile.txt").st_size
    #write the length of the unpadded plaintext file to the start of the
    #ciphertext, so the decrypter knows how many bytes padding to ignore
    fout.write(struct.pack("L",length))
    while True:
        plainblock = bytearray(plaintext.read(16)) #16-byte (128 bit) blocks
        if len(plainblock) == 0:
            #padding seems to be done automatically
            break
        cipherblock = aes_cbc_256.encrypt_block(plainblock)
        cipherblock = "".join([chr(i) for i in cipherblock])
        fout.write(cipherblock)
    fout.close()

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

encrypt(plaintext)
ciphertext = open(r"C:\Users\Philip\python\cryptobox\cipher.txt","rb")
decrypt(ciphertext)
ciphertext.close()
