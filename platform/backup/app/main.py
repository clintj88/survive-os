"""SURVIVE OS Backup Service — FastAPI application.

Also provides a CLI entry point for systemd timer invocation.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from shared.db import connect

from .config import load_config
from .export import create_archive, read_manifest
from .paper import generate_paper_backup
from .restore import restore_full, restore_module, verify_archive
from .snapshot import snapshot_all_modules, snapshot_database
from .status import (
    get_all_last_backups,
    get_backup_history,
    get_drive_status,
    get_last_backup,
    init_status_db,
    record_backup,
)

logger = logging.getLogger("survive.backup")

VERSION = "0.1.0"

config = load_config()
app = FastAPI(title="SURVIVE OS - Backup", version=VERSION)

_status_conn = None


def _get_status_conn():
    global _status_conn
    if _status_conn is None:
        db_path = config.get("status_db", "/var/lib/survive/backup/status.db")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        _status_conn = connect(db_path)
        init_status_db(_status_conn)
    return _status_conn


def _snapshot_dir() -> str:
    return config.get("snapshot_dir", "/var/lib/survive/backup/snapshots")


def _blob_dir() -> str:
    return config.get("blob_dir", "/var/lib/survive/blobs")


def _usb_mount() -> str:
    return config.get("usb_mount", "/mnt/backup")


# --- Health ---

@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "healthy", "version": VERSION})


# --- Snapshot ---

@app.post("/api/backup/snapshot")
async def api_snapshot(body: dict[str, Any] | None = None) -> JSONResponse:
    """Trigger a snapshot of all configured modules."""
    modules = config.get("modules", {})
    if not modules:
        raise HTTPException(400, "No modules configured for backup")

    start = time.time()
    results = snapshot_all_modules(modules, _snapshot_dir())
    duration = time.time() - start

    conn = _get_status_conn()
    for r in results:
        record_backup(
            conn, r["module"], "snapshot", "completed",
            r["size"], duration / max(len(results), 1), r["snapshot"],
        )

    return JSONResponse({"snapshots": results, "duration": round(duration, 2)})


# --- Export ---

@app.post("/api/backup/export")
async def api_export(body: dict[str, Any] | None = None) -> JSONResponse:
    """Create an encrypted backup archive for off-site storage."""
    body = body or {}
    output = body.get("output_path", str(Path(_snapshot_dir()).parent / "export" / "backup.enc"))
    passphrase = body.get("passphrase", config.get("export_passphrase", ""))
    modules = body.get("modules")

    result = create_archive(
        _snapshot_dir(), _blob_dir(), output,
        passphrase=passphrase, modules=modules,
    )
    return JSONResponse(result)


# --- Verify ---

@app.post("/api/backup/verify")
async def api_verify(body: dict[str, Any]) -> JSONResponse:
    """Verify a backup archive's integrity."""
    archive_path = body.get("archive_path", "")
    passphrase = body.get("passphrase", "")
    if not archive_path:
        raise HTTPException(400, "archive_path required")
    result = verify_archive(archive_path, passphrase)
    return JSONResponse(result)


# --- Restore ---

@app.post("/api/backup/restore")
async def api_restore(body: dict[str, Any]) -> JSONResponse:
    """Restore from a backup archive (full or single module)."""
    archive_path = body.get("archive_path", "")
    passphrase = body.get("passphrase", "")
    module = body.get("module")
    restore_dir = body.get("restore_dir", "/var/lib/survive/backup/restore")

    if not archive_path:
        raise HTTPException(400, "archive_path required")

    if module:
        result = restore_module(archive_path, module, restore_dir, passphrase)
    else:
        result = restore_full(archive_path, restore_dir, passphrase)
    return JSONResponse(result)


# --- Paper Backup ---

@app.post("/api/backup/paper")
async def api_paper(body: dict[str, Any] | None = None) -> JSONResponse:
    """Generate printable paper backup with QR codes."""
    body = body or {}
    title = body.get("title", "SURVIVE OS Paper Backup")
    sections = body.get("sections", [])
    include_qr = body.get("include_qr", True)

    html = generate_paper_backup(title, sections, include_qr=include_qr)
    return HTMLResponse(html)


# --- Dashboard ---

@app.get("/api/backup/status")
async def api_status() -> JSONResponse:
    """Backup status dashboard: last backup, sizes, USB health."""
    conn = _get_status_conn()
    backups = get_all_last_backups(conn)
    drive = get_drive_status(_usb_mount())
    return JSONResponse({"backups": backups, "drive": drive})


@app.get("/api/backup/history")
async def api_history(module: str | None = None, limit: int = 50) -> JSONResponse:
    """Get backup history, optionally filtered by module."""
    conn = _get_status_conn()
    history = get_backup_history(conn, module=module, limit=limit)
    return JSONResponse(history)


# --- CLI entry point for systemd timer ---

def run_backup() -> None:
    """Run a full backup cycle: snapshot all modules, create encrypted archive."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

    modules = config.get("modules", {})
    if not modules:
        logger.error("No modules configured for backup")
        sys.exit(1)

    snapshot_dir = _snapshot_dir()
    logger.info("Starting backup of %d modules", len(modules))

    # Snapshot all module databases
    start = time.time()
    results = snapshot_all_modules(modules, snapshot_dir)
    duration = time.time() - start
    logger.info("Snapshots complete: %d modules in %.1fs", len(results), duration)

    # Record status
    conn = _get_status_conn()
    for r in results:
        record_backup(
            conn, r["module"], "snapshot", "completed",
            r["size"], duration / max(len(results), 1), r["snapshot"],
        )

    # Create encrypted archive if passphrase configured
    passphrase = config.get("export_passphrase", "")
    if passphrase:
        export_dir = Path(snapshot_dir).parent / "export"
        export_dir.mkdir(parents=True, exist_ok=True)
        from shared.db.timestamps import utcnow
        timestamp = utcnow().replace(":", "-").replace(".", "-")
        output = str(export_dir / f"backup-{timestamp}.enc")

        logger.info("Creating encrypted archive at %s", output)
        result = create_archive(snapshot_dir, _blob_dir(), output, passphrase=passphrase)
        logger.info("Archive created: %d entries, %d bytes", result["entries"], result["size"])

        # Copy to USB if mounted
        usb_mount = _usb_mount()
        if Path(usb_mount).is_dir():
            import shutil
            usb_dest = Path(usb_mount) / Path(output).name
            shutil.copy2(output, str(usb_dest))
            logger.info("Copied archive to USB: %s", usb_dest)

    logger.info("Backup cycle complete")


if __name__ == "__main__":
    if "--run-backup" in sys.argv:
        run_backup()
    else:
        import uvicorn
        host = config.get("server", {}).get("host", "0.0.0.0")
        port = config.get("server", {}).get("port", 8095)
        uvicorn.run(app, host=host, port=port)
