"""Encrypted backup export for off-site storage.

Packages databases + blobs into a single encrypted archive
with manifest and integrity checksums.
"""

import hashlib
import json
import os
import shutil
import tarfile
import tempfile
from pathlib import Path
from typing import BinaryIO

from shared.db.timestamps import utcnow

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

MANIFEST_NAME = "manifest.json"
CHUNK_SIZE = 64 * 1024


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode(), salt, iterations=100_000)


def create_archive(
    snapshot_dir: str,
    blob_dir: str | None,
    output_path: str,
    passphrase: str = "",
    modules: list[str] | None = None,
) -> dict:
    """Create a backup archive (optionally encrypted).

    Args:
        snapshot_dir: Directory containing database snapshots.
        blob_dir: Optional blob storage directory to include.
        output_path: Path for the output archive.
        passphrase: If provided, encrypt the archive with AES-256-GCM.
        modules: If provided, only include these modules.

    Returns:
        Dict with archive metadata.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    manifest_entries: list[dict] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        tar_path = os.path.join(tmpdir, "backup.tar.gz")

        with tarfile.open(tar_path, "w:gz") as tar:
            # Add database snapshots
            snap_path = Path(snapshot_dir)
            if snap_path.exists():
                for db_file in snap_path.rglob("*.db"):
                    module_name = db_file.parent.name
                    if modules and module_name not in modules:
                        continue
                    arcname = f"databases/{module_name}/{db_file.name}"
                    tar.add(str(db_file), arcname=arcname)
                    manifest_entries.append({
                        "type": "database",
                        "module": module_name,
                        "path": arcname,
                        "sha256": _sha256_file(str(db_file)),
                        "size": db_file.stat().st_size,
                    })

            # Add blobs
            if blob_dir:
                blob_path = Path(blob_dir)
                if blob_path.exists():
                    for blob_file in blob_path.rglob("*"):
                        if blob_file.is_file():
                            rel = blob_file.relative_to(blob_path)
                            arcname = f"blobs/{rel}"
                            tar.add(str(blob_file), arcname=arcname)
                            manifest_entries.append({
                                "type": "blob",
                                "path": arcname,
                                "sha256": _sha256_file(str(blob_file)),
                                "size": blob_file.stat().st_size,
                            })

            # Write manifest into archive
            manifest = {
                "version": "1.0",
                "created_at": utcnow(),
                "entries": manifest_entries,
                "encrypted": bool(passphrase),
            }
            manifest_path = os.path.join(tmpdir, MANIFEST_NAME)
            with open(manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)
            tar.add(manifest_path, arcname=MANIFEST_NAME)

        # Encrypt if passphrase provided
        if passphrase:
            if not HAS_CRYPTO:
                raise ImportError("cryptography library required for encrypted export")
            salt = os.urandom(16)
            key = _derive_key(passphrase, salt)
            nonce = os.urandom(12)
            aesgcm = AESGCM(key)
            with open(tar_path, "rb") as f:
                plaintext = f.read()
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)
            with open(output_path, "wb") as f:
                f.write(salt + nonce + ciphertext)
        else:
            shutil.copy2(tar_path, output_path)

    return {
        "path": output_path,
        "size": os.path.getsize(output_path),
        "encrypted": bool(passphrase),
        "modules": len({e["module"] for e in manifest_entries if e["type"] == "database"}),
        "entries": len(manifest_entries),
        "created_at": manifest["created_at"],
    }


def read_manifest(archive_path: str, passphrase: str = "") -> dict:
    """Read the manifest from a backup archive without fully extracting.

    Args:
        archive_path: Path to the archive file.
        passphrase: Decryption passphrase if encrypted.

    Returns:
        The manifest dict.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tar_path = _decrypt_archive(archive_path, tmpdir, passphrase)
        with tarfile.open(tar_path, "r:gz") as tar:
            member = tar.getmember(MANIFEST_NAME)
            f = tar.extractfile(member)
            if f is None:
                raise ValueError("Manifest not found in archive")
            return json.loads(f.read())


def _decrypt_archive(archive_path: str, tmpdir: str, passphrase: str) -> str:
    """Decrypt an archive if needed, returning path to the tar.gz."""
    if not passphrase:
        return archive_path
    if not HAS_CRYPTO:
        raise ImportError("cryptography library required for decryption")
    with open(archive_path, "rb") as f:
        data = f.read()
    salt = data[:16]
    nonce = data[16:28]
    ciphertext = data[28:]
    key = _derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    tar_path = os.path.join(tmpdir, "backup.tar.gz")
    with open(tar_path, "wb") as f:
        f.write(plaintext)
    return tar_path
