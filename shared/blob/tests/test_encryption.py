"""Tests for blob encryption."""

import pytest

from shared.blob.encryption import HAS_CRYPTO, decrypt_blob, encrypt_blob


@pytest.mark.skipif(not HAS_CRYPTO, reason="cryptography library not installed")
class TestEncryption:
    def test_round_trip(self):
        data = b"sensitive medical data"
        encrypted = encrypt_blob(data, "secret-key")
        assert encrypted != data
        decrypted = decrypt_blob(encrypted, "secret-key")
        assert decrypted == data

    def test_wrong_passphrase(self):
        data = b"private data"
        encrypted = encrypt_blob(data, "correct-key")
        with pytest.raises(Exception):
            decrypt_blob(encrypted, "wrong-key")

    def test_different_encryptions_differ(self):
        data = b"same data"
        e1 = encrypt_blob(data, "key")
        e2 = encrypt_blob(data, "key")
        assert e1 != e2

    def test_empty_data(self):
        encrypted = encrypt_blob(b"", "key")
        assert decrypt_blob(encrypted, "key") == b""
