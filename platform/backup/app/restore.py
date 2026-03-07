"""Restore from backup archives.

Supports full restore, selective (single module) restore,
integrity verification, and schema version handling.
"""

import hashlib
import json
import os
import shutil
import tarfile
import tempfile
from pathlib import Path

from shared.db.timestamps import utcnow

from .export import CHUNK_SIZE, MANIFEST_NAME, _decrypt_archive, _sha256_file


def verify_archive(archive_path: str, passphrase: str = "") -> dict:
    """Verify integrity of a backup archive.

    Returns:
        Dict with "valid" bool, "errors" list, and "manifest".
    """
    errors: list[str] = []
    manifest = None

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            tar_path = _decrypt_archive(archive_path, tmpdir, passphrase)
        except Exception as e:
            return {"valid": False, "errors": [f"Decryption failed: {e}"], "manifest": None}

        try:
            with tarfile.open(tar_path, "r:gz") as tar:
                # Extract manifest
                try:
                    f = tar.extractfile(MANIFEST_NAME)
                    if f is None:
                        errors.append("Manifest file is empty")
                        return {"valid": False, "errors": errors, "manifest": None}
                    manifest = json.loads(f.read())
                except KeyError:
                    errors.append("No manifest.json in archive")
                    return {"valid": False, "errors": errors, "manifest": None}

                # Verify each entry
                for entry in manifest.get("entries", []):
                    path = entry["path"]
                    expected_hash = entry["sha256"]
                    try:
                        member = tar.getmember(path)
                        ef = tar.extractfile(member)
                        if ef is None:
                            errors.append(f"Cannot read {path}")
                            continue
                        h = hashlib.sha256()
                        while True:
                            chunk = ef.read(CHUNK_SIZE)
                            if not chunk:
                                break
                            h.update(chunk)
                        if h.hexdigest() != expected_hash:
                            errors.append(f"Checksum mismatch: {path}")
                    except KeyError:
                        errors.append(f"Missing from archive: {path}")
        except tarfile.TarError as e:
            errors.append(f"Archive corrupt: {e}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "manifest": manifest,
    }


def restore_full(
    archive_path: str,
    restore_dir: str,
    passphrase: str = "",
) -> dict:
    """Restore all databases and blobs from an archive.

    Args:
        archive_path: Path to the backup archive.
        restore_dir: Directory to extract files into.
        passphrase: Decryption passphrase if encrypted.

    Returns:
        Dict with restore metadata.
    """
    Path(restore_dir).mkdir(parents=True, exist_ok=True)
    restored: list[str] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        tar_path = _decrypt_archive(archive_path, tmpdir, passphrase)
        with tarfile.open(tar_path, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name == MANIFEST_NAME:
                    continue
                tar.extract(member, path=restore_dir, filter="data")
                restored.append(member.name)

    return {
        "restore_dir": restore_dir,
        "files_restored": len(restored),
        "restored_at": utcnow(),
    }


def restore_module(
    archive_path: str,
    module_name: str,
    restore_dir: str,
    passphrase: str = "",
) -> dict:
    """Restore a single module's data from an archive.

    Args:
        archive_path: Path to the backup archive.
        module_name: Name of the module to restore.
        restore_dir: Directory to extract files into.
        passphrase: Decryption passphrase if encrypted.

    Returns:
        Dict with restore metadata.
    """
    Path(restore_dir).mkdir(parents=True, exist_ok=True)
    restored: list[str] = []
    prefix = f"databases/{module_name}/"

    with tempfile.TemporaryDirectory() as tmpdir:
        tar_path = _decrypt_archive(archive_path, tmpdir, passphrase)
        with tarfile.open(tar_path, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.startswith(prefix):
                    tar.extract(member, path=restore_dir, filter="data")
                    restored.append(member.name)

    return {
        "module": module_name,
        "restore_dir": restore_dir,
        "files_restored": len(restored),
        "restored_at": utcnow(),
    }
