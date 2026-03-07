"""Tests for blob encryption."""

import pytest

from shared.blob.encryption import HAS_CRYPTO, decrypt_blob, encrypt_blob


@pytest.mark.skipif(not HAS_CRYPTO, reason="cryptography library not installed")
def test_encrypt_decrypt_roundtrip():
    data = b"sensitive medical data"
    passphrase = "test-secret"
    encrypted = encrypt_blob(data, passphrase)
    assert encrypted != data
    decrypted = decrypt_blob(encrypted, passphrase)
    assert decrypted == data


@pytest.mark.skipif(not HAS_CRYPTO, reason="cryptography library not installed")
def test_wrong_passphrase():
    data = b"secret"
    encrypted = encrypt_blob(data, "correct")
    with pytest.raises(Exception):  # InvalidTag from cryptography
        decrypt_blob(encrypted, "wrong")


@pytest.mark.skipif(not HAS_CRYPTO, reason="cryptography library not installed")
def test_different_encryptions_differ():
    data = b"same data"
    enc1 = encrypt_blob(data, "pass")
    enc2 = encrypt_blob(data, "pass")
    # Random salt+nonce means different ciphertext each time
    assert enc1 != enc2
