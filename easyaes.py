import os, hashlib, struct
from aespython import key_expander, aes_cipher, cbc_mode

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

def encrypt(password,fin=None,path=None,plaintext=None,plainlist=None):
    #outputs ciphertext as a string
    if fin:
        plaintext = fin.read()
    elif path:
        plaintext = open(path,"rb").read() #don't worry, I think the garbage collector closes it automatically
    elif plainlist:
        plaintext = "".join(cipherlist)
    
    length = len(plaintext) #get file length, so the decrypter knows how many bytes padding to ignore
    #CREATE AN IV AND STORE ITS KEY FOR GENERATION WHEN IT'S DECRYPTION TIME
    ivkey = os.urandom(16)
    iv = bytearray(sha(ivkey+password)[:16])
    aes_cbc_256.set_iv(iv)  
    
    out = list(ivkey+struct.pack("L",length))
    cursor = 0
    while cursor < length:
        plainblock = bytearray(plaintext[cursor:cursor+16]) #16-byte blocks
        cipherblock = aes_cbc_256.encrypt_block(plainblock)
        out.extend(cipherblock)
        cursor += 16
    return str(bytearray(out))

def decrypt(password,fin=None,path=None,ciphertext=None,cipherlist=None):
    #takes a file, string, path string or list ciphertext
    #returns decrypted data as a string
    if fin:
        ciphertext = fin.read()
    elif path:
        ciphertext = open(path,"rb").read() #don't worry, I think the garbage collector closes it automatically
    elif cipherlist:
        ciphertext = "".join(cipherlist)
        
    ivkey = ciphertext[:16]
    iv = bytearray(sha(ivkey+password)[:16])
    aes_cbc_256.set_iv(iv)
    length = struct.unpack("L",ciphertext[16:16+struct.calcsize("L")])[0]
    blocks = 0
    plainblock = ""
    out = []

    cursor = 20
    while cursor-20 < len(ciphertext):
        #reading from a string (never mind lists of blocks, that never happens)
        cipherblock = list(bytearray(ciphertext[cursor:cursor+16]))
        plainblock = aes_cbc_256.decrypt_block(cipherblock)
        out.extend(plainblock)
        cursor += 16
    
    #remove padding:
    del out[length:]
    return str(bytearray(out))


aes_cbc_256 = None
