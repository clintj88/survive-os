"""Optional encryption at rest for sensitive blobs.

Uses AES-256-GCM via the cryptography library when available,
falls back to a no-op for unencrypted modules.
"""

import hashlib
import os
from typing import Protocol

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

NONCE_SIZE = 12  # 96-bit nonce for AES-GCM


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from a passphrase using PBKDF2."""
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode(), salt, iterations=100_000)


def encrypt_blob(data: bytes, passphrase: str) -> bytes:
    """Encrypt blob data with AES-256-GCM.

    Returns: salt (16) + nonce (12) + ciphertext+tag
    Raises ImportError if cryptography library is not installed.
    """
    if not HAS_CRYPTO:
        raise ImportError("cryptography library required for blob encryption")
    salt = os.urandom(16)
    key = _derive_key(passphrase, salt)
    nonce = os.urandom(NONCE_SIZE)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return salt + nonce + ciphertext


def decrypt_blob(encrypted: bytes, passphrase: str) -> bytes:
    """Decrypt blob data encrypted with encrypt_blob().

    Raises ImportError if cryptography library is not installed.
    Raises cryptography.exceptions.InvalidTag if passphrase is wrong.
    """
    if not HAS_CRYPTO:
        raise ImportError("cryptography library required for blob decryption")
    salt = encrypted[:16]
    nonce = encrypted[16:16 + NONCE_SIZE]
    ciphertext = encrypted[16 + NONCE_SIZE:]
    key = _derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)
