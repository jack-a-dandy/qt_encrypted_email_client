from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA1
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto import Random
from Crypto.PublicKey import DSA
from Crypto.Signature import DSS
import codecs
from Crypto.Cipher import AES
from Crypto import Random
import os
import sys


class RSACipher():

    def generate(self):
        modulus_length = 256*4
        privatekey = RSA.generate(modulus_length, Random.new().read)
        publickey = privatekey.publickey()
        return privatekey, publickey

    def encrypt(self, key, raw):
        public_key = RSA.importKey(key)
        cipher = PKCS1_OAEP.new(public_key)
        return cipher.encrypt(raw)

    def decrypt(self, key, enc):
        private_key = RSA.importKey(key)
        cipher = PKCS1_OAEP.new(private_key)
        return cipher.decrypt(enc)


class DSACipher():

    def generate(self):
        privatekey = DSA.generate(2048)
        return privatekey, privatekey.publickey()

    def sign(self, key, data):
        tag = SHA1.new(data)
        signer = DSS.new(DSA.import_key(key), 'fips-186-3')
        signature = signer.sign(tag)
        return signature

    def verify(self, key, data, signature):
        public_key = DSA.import_key(key)
        hash_value = SHA1.new(data)
        verifier = DSS.new(public_key, 'fips-186-3')
        try:
            verifier.verify(hash_value, signature)
            return True
        except:
            return False


class AESCipher:

    def generate(self):
        return os.urandom(32)

    def encrypt(self, key, data):
        bs = AES.block_size
        iv = Random.new().read(bs)
        ivSize = (len(iv)).to_bytes(4, byteorder="little", signed=False)
        res=ivSize
        res+=iv
        finished = False
        cipher = AES.new(key, AES.MODE_CFB, iv)
        j = 0
        while not finished:
            chunk = data[:j+ 2048 * bs]
            j+=2048*bs
            if len(chunk) == 0 or len(chunk) % bs != 0:
                #PKCS7 padding:
                padding_length = (bs - len(chunk) % bs) or bs
                padl = 0
                while padl < padding_length:
                    chunk += padding_length.to_bytes(1, byteorder="little", signed=False)
                    padl += 1
                finished = True
            res+=cipher.encrypt(chunk)
        return res

    def decrypt(self, key, data):
        sizeIVb = data[:4]
        sizeIV = int.from_bytes(sizeIVb, byteorder="little", signed=False)
        iv = data[4:4+sizeIV]
        cipher = AES.new(key, AES.MODE_CFB, iv)
        next_chunk = ''
        bs = AES.block_size
        finished = False
        j = 4+sizeIV
        outd = b''
        while not finished:
            chunk, next_chunk = next_chunk, cipher.decrypt(data[j:j+2048 * bs])
            j+=2048*bs
            if type(chunk) == type(''):
                if sys.version[0]=="2":
                    chunk = codecs.encode(codecs.decode(chunk, "utf-8"), "utf-8")
                else:
                    chunk = codecs.encode(chunk, "utf-8")
            if len(next_chunk) == 0:
                     #remove PKCS7 padding
                if sys.version[0] == "2":
                    padding_length = ord(chunk[-1])
                else:
                    padding_length = chunk[-1]
                chunk = chunk[:-padding_length]
                finished = True
            outd+=chunk
        return outd