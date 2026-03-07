# Epidemic Surveillance - SURVIVE OS Medical Module

Offline-first epidemic surveillance for post-infrastructure communities. Tracks syndromic data, generates threshold-based alerts, manages contact tracing and quarantines, and shares anonymized data across communities.

## Features

- **Syndromic Surveillance**: Track symptom reports by syndrome category with daily/weekly aggregation and rolling baseline calculation
- **Automated Alerts**: Threshold detection (watch/warning/critical) with Redis pub/sub for cross-module notification
- **Cross-Community Sharing**: Anonymized aggregate data export and ham radio broadcast via Redis
- **Contact Tracing**: Record and visualize contact networks with exposure risk scoring
- **Quarantine Management**: Track isolation status, daily check-ins, and supply needs
- **Historical Timeline**: Record epidemic events for pattern recognition and lessons learned

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8040
```

## Configuration

Copy `epidemic.yml` to `/etc/survive/epidemic.yml` and update the SQLCipher key.

## API

- `GET /health` - Health check
- `GET/POST /api/surveillance/reports` - Symptom reports CRUD
- `GET /api/surveillance/counts` - Aggregated counts
- `GET /api/surveillance/baseline` - Rolling baseline
- `GET/POST /api/alerts` - Alert management
- `POST /api/alerts/check` - Run threshold check
- `GET/POST /api/contacts` - Contact tracing
- `GET /api/contacts/network/{case_id}` - Contact network
- `GET/POST /api/quarantine` - Quarantine management
- `GET /api/quarantine/census` - Quarantine census
- `GET/POST /api/timeline/events` - Historical events
- `GET /api/sharing/export` - Anonymized data export
- `POST /api/sharing/broadcast` - Ham radio broadcast

## Encryption

Production uses SQLCipher (pysqlcipher3) for encryption at rest. Falls back to standard sqlite3 for development and testing.

## Port

8040 (Medical - encrypted)
