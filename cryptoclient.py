#CryptoBox client
import socket, ssl, os, hashlib, struct
from easyaes import encrypt, decrypt


plaintext = open(r"C:\Users\Philip\python\cryptobox\testfile.txt","rb")
iv = bytearray(hashlib.sha512("password").digest()[:16])

outfile = open(r"C:\Users\Philip\python\cryptobox\cipher.txt","wb")
outpath = r"C:\Users\Philip\python\cryptobox\cipher.txt"
#outlist = []
encrypt(plaintext,outfile,iv)
ciphertext = open(r"C:\Users\Philip\python\cryptobox\cipher.txt","rb")
decrypt(ciphertext,r"C:\Users\Philip\python\cryptobox\decrypted.txt",iv)
ciphertext.close()
