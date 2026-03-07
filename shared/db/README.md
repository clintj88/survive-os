# shared/db — SURVIVE OS Database Foundation

Shared Python library for SQLite/SQLCipher database access. All modules import from this package instead of maintaining per-module `database.py` files.

## Installation

```bash
pip install -r requirements.txt
```

Note: `pysqlcipher3` requires `libsqlcipher-dev` on Debian/Ubuntu. Without it, the library falls back to standard `sqlite3` (no encryption).

## Quick Start

```python
from shared.db import connect, execute, query, generate_id, utcnow, SchemaManager

# Open a database (plain SQLite)
conn = connect("/var/lib/survive/mymodule/data.db")

# Open an encrypted database (SQLCipher)
conn = connect("/var/lib/survive/medical/data.db", key="secret")

# Generate a time-ordered UUID v7 for record IDs
record_id = generate_id()  # e.g. "0190a5e8..."

# Get current UTC timestamp
now = utcnow()  # "2026-03-07T12:00:00.000000Z"
```

## API Reference

### engine — Connection & Query Helpers

| Function | Description |
|---|---|
| `connect(db_path, key="", wal_mode=True, foreign_keys=True)` | Create a configured SQLite/SQLCipher connection |
| `query(conn, sql, params=())` | Execute SELECT, return list of dicts |
| `execute(conn, sql, params=())` | Execute INSERT/UPDATE/DELETE, return lastrowid |
| `executemany(conn, sql, param_seq)` | Execute with multiple parameter sets |
| `executescript(conn, sql)` | Execute multi-statement SQL script |

### ids — Record ID Generation

| Function | Description |
|---|---|
| `generate_id()` | Generate a UUID v7 (time-ordered) hex string |
| `uuid7()` | UUID v7 explicitly |
| `uuid4()` | Standard UUID v4 hex string |

### timestamps — UTC Time Helpers

| Function | Description |
|---|---|
| `utcnow()` | Current UTC as ISO 8601 string |
| `parse_timestamp(value)` | Parse ISO 8601 string to datetime |
| `to_iso(dt)` | Convert datetime to ISO 8601 UTC string |

### schema — Migration System

```python
sm = SchemaManager(conn, module="mymodule")
sm.add_migration(
    version=1,
    description="create items table",
    up=lambda c: c.executescript("CREATE TABLE items (id TEXT PRIMARY KEY, name TEXT)"),
    down=lambda c: c.executescript("DROP TABLE items"),
)
sm.migrate_up()           # Apply all pending
sm.migrate_down(0)        # Roll back to version 0
sm.current_version()      # -> 1
sm.pending_migrations()   # -> []
```

### soft_delete — Soft Delete Helpers

```python
from shared.db import soft_delete_sql, filter_deleted, utcnow

# Mark a record as deleted
conn.execute(soft_delete_sql("items"), (utcnow(), record_id))

# Query excluding deleted records (default)
sql = filter_deleted("SELECT * FROM items")
# -> "SELECT * FROM items WHERE deleted_at IS NULL"

# Include deleted records
sql = filter_deleted("SELECT * FROM items", include_deleted=True)
```

### vector_clock — CRDT Ordering

```python
from shared.db import VectorClock

vc1 = VectorClock()
vc1.increment("node-a")  # -> 1
vc1.increment("node-a")  # -> 2

vc2 = VectorClock({"node-b": 1})

merged = vc1.merge(vc2)  # VectorClock({"node-a": 2, "node-b": 1})

# Serialize for DB storage
json_str = vc1.to_json()
restored = VectorClock.from_json(json_str)
```

### backup — SQLite Online Backup

```python
from shared.db import connect, backup_to_file, restore_from_file

conn = connect("/var/lib/survive/mymodule/data.db")
backup_to_file(conn, "/backups/mymodule-2026-03-07.db")

# Encrypted backup
backup_to_file(conn, "/backups/mymodule.db.enc", dest_key="backup-secret")

# Restore
restore_from_file("/backups/mymodule-2026-03-07.db", conn)
```

## Running Tests

```bash
cd shared/db
python -m pytest tests/ -v
```
