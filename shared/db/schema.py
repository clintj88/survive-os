"""Schema versioning with forward/backward migration support.

Tracks current version in a `_schema_versions` table per module.
Provides migrate_up() and migrate_down() helpers.
"""

import sqlite3
from dataclasses import dataclass
from typing import Callable

from .timestamps import utcnow

MigrationFn = Callable[[sqlite3.Connection], None]

_SCHEMA_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS _schema_versions (
    version INTEGER PRIMARY KEY,
    module TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    applied_at TEXT NOT NULL,
    rolled_back_at TEXT DEFAULT NULL
)
"""


@dataclass(frozen=True, slots=True)
class Migration:
    """A single schema migration with up and down functions."""
    version: int
    description: str
    up: MigrationFn
    down: MigrationFn


class SchemaManager:
    """Manages schema versioning and migrations for a module."""

    def __init__(self, conn: sqlite3.Connection, module: str) -> None:
        self.conn = conn
        self.module = module
        self._migrations: list[Migration] = []
        self._ensure_schema_table()

    def _ensure_schema_table(self) -> None:
        self.conn.executescript(_SCHEMA_TABLE_SQL)

    def add_migration(self, version: int, description: str, up: MigrationFn, down: MigrationFn) -> None:
        """Register a migration. Versions must be unique and added in order."""
        self._migrations.append(Migration(version=version, description=description, up=up, down=down))
        self._migrations.sort(key=lambda m: m.version)

    def current_version(self) -> int:
        """Get the current schema version (0 if no migrations applied)."""
        row = self.conn.execute(
            "SELECT MAX(version) as v FROM _schema_versions WHERE module = ? AND rolled_back_at IS NULL",
            (self.module,),
        ).fetchone()
        return row["v"] if row and row["v"] is not None else 0

    def migrate_up(self, target_version: int | None = None) -> list[int]:
        """Apply all pending migrations up to target_version (or latest).

        Returns list of versions applied.
        """
        current = self.current_version()
        applied: list[int] = []

        for migration in self._migrations:
            if migration.version <= current:
                continue
            if target_version is not None and migration.version > target_version:
                break
            migration.up(self.conn)
            self.conn.execute(
                "INSERT INTO _schema_versions (version, module, description, applied_at) VALUES (?, ?, ?, ?)",
                (migration.version, self.module, migration.description, utcnow()),
            )
            self.conn.commit()
            applied.append(migration.version)

        return applied

    def migrate_down(self, target_version: int = 0) -> list[int]:
        """Roll back migrations down to target_version.

        Returns list of versions rolled back.
        """
        current = self.current_version()
        rolled_back: list[int] = []

        for migration in reversed(self._migrations):
            if migration.version <= target_version:
                break
            if migration.version > current:
                continue
            migration.down(self.conn)
            self.conn.execute(
                "UPDATE _schema_versions SET rolled_back_at = ? WHERE version = ? AND module = ?",
                (utcnow(), migration.version, self.module),
            )
            self.conn.commit()
            rolled_back.append(migration.version)

        return rolled_back

    def pending_migrations(self) -> list[Migration]:
        """Return list of migrations not yet applied."""
        current = self.current_version()
        return [m for m in self._migrations if m.version > current]
