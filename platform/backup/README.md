# platform/backup — Automated Backup System

Backup service for all SURVIVE OS module databases and blob stores. Supports point-in-time snapshots, encrypted archives for off-site storage, integrity verification, and paper backups.

## Features

- **Snapshots**: Online SQLite backup API for consistent copies without stopping services
- **Encrypted export**: AES-256-GCM archives with integrity manifests for USB transport
- **Restore**: Full or per-module restore with integrity verification
- **Paper backups**: Printable HTML with QR codes for re-digitization
- **Status dashboard**: Backup history, sizes, USB drive health
- **Systemd timers**: Daily automated backups at 2:00 AM

## Configuration

Copy `backup.yml` to `/etc/survive/backup.yml` and configure module paths.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/backup/snapshot` | Trigger snapshot of all modules |
| POST | `/api/backup/export` | Create encrypted archive |
| POST | `/api/backup/verify` | Verify archive integrity |
| POST | `/api/backup/restore` | Restore from archive |
| GET | `/api/backup/status` | Backup status for all modules |
| GET | `/api/backup/history` | Backup history |

## Running

```bash
uvicorn platform.backup.app.main:app --host 127.0.0.1 --port 8095
```

## Tests

```bash
python3 -m pytest platform/backup/tests/ -v
```
