import binascii
import random
import string
from django.conf import settings


def encrypt_if_not_encrypted(value):
    encryptor = Encryptor()
    if isinstance(value, EncryptedString):
        return value
    else:
        encrypted = encryptor.encrypt(value)
        return EncryptedString(encrypted)


def decrypt_if_not_decrypted(value):
    encryptor = Encryptor()
    if isinstance(value, DecryptedString):
        return value
    else:
        encrypted = encryptor.decrypt(value)
        return DecryptedString(encrypted)


class EncryptedString(str):
    pass


class DecryptedString(str):
    pass


class Encryptor(object):
    def __init__(self):
        imp = __import__('Crypto.Cipher', globals(), locals(), ['AES'], -1)
        self.cipher = getattr(imp, 'AES').new(settings.SECRET_KEY[:32])

    def decrypt(self, value):
        #values should always be encrypted no matter what!
        #raise an error if things may have been tampered with
        try:
            decrypted_value = self.cipher.decrypt(binascii.a2b_hex(str(value))).split('\0')[0]
        except TypeError:
            decrypted_value = value
        return decrypted_value

    def encrypt(self, value):
        padding = None
        if value is not None and not isinstance(value, EncryptedString):
            padding = self.cipher.block_size - len(value) % self.cipher.block_size
        if padding and padding < self.cipher.block_size:
            value += "\0" + ''.join([random.choice(string.printable) for index in range(padding-1)])
        value = EncryptedString(binascii.b2a_hex(self.cipher.encrypt(value)))
        return value
