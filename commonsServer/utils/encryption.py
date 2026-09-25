from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from django.conf import settings
import base64
import os

# Marker prepended to data encrypted with the new AES-GCM scheme so that
# decrypt_data() can tell it apart from data encrypted with the legacy
# (now deprecated) AES-CFB scheme.
_GCM_MARKER = b"GCM1"
_GCM_NONCE_SIZE = 12  # recommended nonce size for AES-GCM


def encrypt_data(plain_text):
    """
    Encrypt the plain text using AES-GCM encryption (authenticated).
    """
    if not plain_text:
        return None
    nonce = os.urandom(_GCM_NONCE_SIZE)
    aesgcm = AESGCM(settings.VARIABLE_SECRET_KEY)
    encrypted_data = aesgcm.encrypt(nonce, plain_text.encode(), None)
    return base64.urlsafe_b64encode(_GCM_MARKER + nonce + encrypted_data).decode()


def decrypt_data(encrypted_text):
    """
    Decrypt data encrypted with encrypt_data().

    Supports both the current AES-GCM format and the legacy AES-CFB format
    (kept for backward compatibility so previously stored/encrypted data
    remains readable).
    """
    if not encrypted_text:
        return None
    encrypted_text_bytes = base64.urlsafe_b64decode(encrypted_text)

    if encrypted_text_bytes.startswith(_GCM_MARKER):
        payload = encrypted_text_bytes[len(_GCM_MARKER):]
        nonce = payload[:_GCM_NONCE_SIZE]
        ciphertext = payload[_GCM_NONCE_SIZE:]
        aesgcm = AESGCM(settings.VARIABLE_SECRET_KEY)
        return aesgcm.decrypt(nonce, ciphertext, None).decode()

    # Legacy format: AES-CFB with a 16 byte IV prepended to the ciphertext
    # BEFORE REMOVING
    # BE SURE THAT ALL PROTECTED VARIABLES
    # HAVE MIGRATED


    iv = encrypted_text_bytes[:16]
    cipher = Cipher(algorithms.AES(settings.VARIABLE_SECRET_KEY), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(encrypted_text_bytes[16:]) + decryptor.finalize()
    return decrypted_data.decode()