# SURVIVE OS Emergency Alerts

Emergency alert system with multi-tier broadcast, acknowledgment tracking, and audit logging.

## Features

- Create and broadcast alerts with severity levels (info, warning, critical, emergency)
- Multi-tier broadcast via Redis pub/sub: local network, Meshtastic mesh, ham radio
- Alert acknowledgment tracking per user
- Alert resolution with audit trail
- Role-based alert creation (admin, security roles from LLDAP)
- Graceful degradation when Redis is unavailable

## API

- `GET /health` - Health check
- `GET /api/alerts` - List alerts (filter by `?active=true` or `?severity=critical`)
- `POST /api/alerts` - Create and broadcast alert
- `GET /api/alerts/{id}` - Get alert with acks and broadcast log
- `POST /api/alerts/{id}/resolve` - Resolve alert
- `POST /api/alerts/{id}/ack` - Acknowledge alert
- `GET /api/alerts/{id}/acks` - List acknowledgments

## Configuration

Copy `alerts.yml` to `/etc/survive/alerts.yml`.

## Running

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8011
```

## Testing

```bash
pytest tests/
```
