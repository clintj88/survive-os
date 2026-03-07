"""Soft delete helpers. Records are marked deleted, never physically removed."""


SOFT_DELETE_COLUMNS = """
    deleted_at TEXT DEFAULT NULL
"""

NOT_DELETED = "deleted_at IS NULL"


def soft_delete_sql(table: str, id_column: str = "id") -> str:
    """Return SQL to soft-delete a record by setting deleted_at."""
    return f"UPDATE {table} SET deleted_at = ? WHERE {id_column} = ?"


def filter_deleted(base_query: str, include_deleted: bool = False) -> str:
    """Append a soft-delete filter to a query if needed.

    If the query already has a WHERE clause, appends with AND.
    Otherwise adds WHERE deleted_at IS NULL.
    """
    if include_deleted:
        return base_query
    upper = base_query.upper()
    if "WHERE" in upper:
        return f"{base_query} AND deleted_at IS NULL"
    return f"{base_query} WHERE deleted_at IS NULL"
