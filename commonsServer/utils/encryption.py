from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from django.conf import settings
import base64
import os

def encrypt_data(plain_text):
    """
    Encrypt the plain text using AES encryption.
    """
    if not plain_text:
        return None
    iv = os.urandom(16)  # AES block size is 16 bytes
    cipher = Cipher(algorithms.AES(settings.VARIABLE_SECRET_KEY), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(plain_text.encode()) + encryptor.finalize()
    return base64.urlsafe_b64encode(iv + encrypted_data).decode()


def decrypt_data(encrypted_text):
    """
    Decrypt the encrypted text using AES encryption.
    """
    if not encrypted_text:
        return None
    encrypted_text_bytes = base64.urlsafe_b64decode(encrypted_text)
    iv = encrypted_text_bytes[:16]
    cipher = Cipher(algorithms.AES(settings.VARIABLE_SECRET_KEY), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(encrypted_text_bytes[16:]) + decryptor.finalize()
    return decrypted_data.decode()