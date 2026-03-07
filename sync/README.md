# SURVIVE OS — CRDT Sync Engine

Offline-first data synchronization using CRDT (Conflict-free Replicated Data Types) with vector clocks for causal ordering and last-writer-wins conflict resolution.

## Architecture

```
                    +-----------+
                    |  Hub Node |
                    | (coord.)  |
                    +-----+-----+
                   /      |      \
          +-------+  +---+---+  +-------+
          | Spoke |  | Spoke |  |Gateway|
          | Node  |  | Node  |  | Node  |
          +-------+  +-------+  +---+---+
                                    |
                              (ham / sneakernet)
                                    |
                                +---+---+
                                |Gateway|
                                | Node  |
                                +---+---+
                                    |
                              +-----+-----+
                              |  Hub Node |
                              | (remote)  |
                              +-----------+
```

### Sync Topology

- **Hub-Spoke** within a community — hub coordinates all sync
- **Spoke** nodes only sync with their community's hub
- **Gateway** nodes bridge communities over ham radio or sneakernet

### Sync Protocol

1. **Handshake** — nodes exchange vector clocks to determine what's needed
2. **Document Exchange** — missing/updated documents sent as snapshots
3. **Acknowledgment** — receiver confirms merge success
4. **Idempotent** — receiving the same data twice produces identical state

### Transport Layers

| Transport | Use Case | Format |
|-----------|----------|--------|
| TCP/mDNS  | Local network peers | JSON over TCP |
| Redis     | Same-node inter-module | JSON pub/sub |
| Serial    | Ham radio / sneakernet | Binary chunked |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/status` | Node status and sync summary |
| POST | `/api/documents` | Create a document |
| GET | `/api/documents/{id}` | Get a document |
| PATCH | `/api/documents/{id}` | Update a document |
| DELETE | `/api/documents/{id}` | Delete a document |
| GET | `/api/documents` | List documents (filter by type/since) |
| POST | `/api/sync/handshake` | Sync handshake |
| POST | `/api/sync/push` | Push documents to this node |
| GET | `/api/peers` | List all peers |
| GET | `/api/peers/online` | List online peers |
| POST | `/api/peers` | Add a peer |
| DELETE | `/api/peers/{id}` | Remove a peer |

## Configuration

Copy `sync.yml` to `/etc/survive/sync.yml` and configure:

- `node.role` — `hub`, `spoke`, or `gateway`
- `node.community` — community identifier
- `transport.tcp.enabled` — enable TCP sync
- `transport.redis.enabled` — enable Redis pub/sub
- `discovery.mdns_enabled` — enable mDNS peer discovery

## Running

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8100
```

## Testing

```bash
pip install pytest
pytest tests/ -v
```

## Port

- Sync API: 8100
- Sync TCP transport: 8101
