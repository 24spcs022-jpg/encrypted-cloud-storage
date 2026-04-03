from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

def generate_rsa_keys():
    key = RSA.generate(2048)
    return key.export_key(), key.publickey().export_key()

def rsa_encrypt(public_key, data):
    return PKCS1_OAEP.new(RSA.import_key(public_key)).encrypt(data)

def rsa_decrypt(private_key, data):
    return PKCS1_OAEP.new(RSA.import_key(private_key)).decrypt(data)

def aes_encrypt(data):
    key = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_EAX)
    encrypted, tag = cipher.encrypt_and_digest(data)
    return key, cipher.nonce, tag, encrypted

def aes_decrypt(key, nonce, tag, encrypted):
    cipher = AES.new(key, AES.MODE_EAX, nonce)
    return cipher.decrypt_and_verify(encrypted, tag)
