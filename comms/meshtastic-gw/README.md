# Meshtastic Gateway - SURVIVE OS Comms Module

Gateway daemon that bridges Meshtastic mesh radio networks to the SURVIVE OS platform via Redis pub/sub.

## Features

- Serial and BLE connections to Meshtastic radios
- Message bridging: mesh <-> Redis pub/sub (`comms.meshtastic`)
- SQLite message history
- Radio provisioning UI (assign radios to LLDAP users)
- Mesh network topology view
- Auto-reconnect on connection loss

## Setup

```bash
pip install -r requirements.txt
cp meshtastic-gw.yml /etc/survive/meshtastic-gw.yml
uvicorn app.main:app --host 0.0.0.0 --port 8012
```

## API Endpoints

- `GET /health` - Health check
- `GET /api/messages` - List messages (query: `channel`, `limit`, `offset`)
- `POST /api/messages` - Send a message (JSON: `content`, `recipient`, `channel`)
- `GET /api/status` - Gateway status
- `GET /api/provisioning/radios` - List known radios
- `GET /api/provisioning/radios/scan` - Scan for radios
- `POST /api/provisioning/radios/assign` - Assign radio to user
- `GET /api/provisioning/users` - List LLDAP users
- `GET /api/provisioning/channels` - List channels
- `GET /api/provisioning/topology` - Mesh topology

## Configuration

See `meshtastic-gw.yml` for all options. Copy to `/etc/survive/meshtastic-gw.yml`.

## Testing

```bash
pip install pytest httpx
pytest tests/
```
