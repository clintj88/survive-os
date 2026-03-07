"""Shared database foundation library for SURVIVE OS.

All modules import from this package instead of maintaining
per-module database.py files.
"""

from .backup import backup_to_file, restore_from_file
from .engine import connect, execute, executemany, executescript, query
from .ids import generate_id, uuid4, uuid7
from .schema import Migration, SchemaManager
from .soft_delete import NOT_DELETED, SOFT_DELETE_COLUMNS, filter_deleted, soft_delete_sql
from .timestamps import parse_timestamp, to_iso, utcnow
from .vector_clock import VectorClock

__all__ = [
    # engine
    "connect",
    "query",
    "execute",
    "executemany",
    "executescript",
    # ids
    "generate_id",
    "uuid7",
    "uuid4",
    # timestamps
    "utcnow",
    "parse_timestamp",
    "to_iso",
    # soft_delete
    "SOFT_DELETE_COLUMNS",
    "NOT_DELETED",
    "soft_delete_sql",
    "filter_deleted",
    # vector_clock
    "VectorClock",
    # schema
    "SchemaManager",
    "Migration",
    # backup
    "backup_to_file",
    "restore_from_file",
]
