# platform/backup — Automated Backup System

Backup service for all SURVIVE OS module databases and blob stores. Supports point-in-time snapshots, encrypted archives for off-site storage, integrity verification, selective restore, and paper backups with QR codes.

## Features

- **Snapshots**: Online SQLite backup API for consistent copies without stopping services
- **Encrypted export**: AES-256-GCM archives with integrity manifests for USB transport
- **Restore**: Full or per-module restore with integrity verification
- **Paper backups**: Printable HTML with QR codes for re-digitization of critical data
- **Status dashboard**: Backup history, sizes, durations, USB drive health
- **Systemd timers**: Daily automated backups at 2:00 AM (not cron)
- **CLI mode**: `--run-backup` flag for timer-triggered full backup cycles

## Architecture

```
app/
  main.py        — FastAPI service + CLI entry point
  config.py      — YAML config loader with defaults
  snapshot.py    — SQLite online backup API snapshots
  export.py      — Encrypted archive creation (AES-256-GCM)
  restore.py     — Full/selective restore with integrity checks
  paper.py       — Printable HTML + QR code generation
  status.py      — Backup history tracking in SQLite
  scheduler.py   — Systemd unit file generation
```

## Configuration

Copy `backup.yml` to `/etc/survive/backup.yml` and configure module paths.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/backup/snapshot` | Trigger snapshot of all modules |
| POST | `/api/backup/export` | Create encrypted archive |
| POST | `/api/backup/verify` | Verify archive integrity |
| POST | `/api/backup/restore` | Restore from archive (full or single module) |
| POST | `/api/backup/paper` | Generate printable paper backup with QR codes |
| GET | `/api/backup/status` | Backup status dashboard |
| GET | `/api/backup/history` | Backup history (filterable by module) |

## Systemd Setup

```bash
# API service (always running)
sudo cp survive-backup.service /etc/systemd/system/
sudo systemctl enable --now survive-backup.service

# Daily backup timer
sudo cp survive-backup-run.service /etc/systemd/system/
sudo cp survive-backup.timer /etc/systemd/system/
sudo systemctl enable --now survive-backup.timer
```

## Running

```bash
# API server
uvicorn platform.backup.app.main:app --host 127.0.0.1 --port 8095

# Manual backup run (same as timer invokes)
python3 -m platform.backup.app.main --run-backup
```

## Tests

```bash
python3 -m pytest platform/backup/tests/ -v
```
