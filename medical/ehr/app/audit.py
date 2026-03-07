"""Audit logging for EHR access and modifications."""

from .database import execute, query


def log_action(
    user_name: str,
    action: str,
    resource_type: str,
    resource_id: str = "",
    details: str = "",
) -> None:
    """Record an audit log entry."""
    execute(
        "INSERT INTO audit_log (user_name, action, resource_type, resource_id, details) VALUES (?, ?, ?, ?, ?)",
        (user_name, action, resource_type, resource_id, details),
    )


def get_audit_log(limit: int = 100, resource_type: str = "", resource_id: str = "") -> list[dict]:
    """Retrieve audit log entries."""
    sql = "SELECT * FROM audit_log"
    conditions: list[str] = []
    params: list = []
    if resource_type:
        conditions.append("resource_type = ?")
        params.append(resource_type)
    if resource_id:
        conditions.append("resource_id = ?")
        params.append(resource_id)
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    return query(sql, tuple(params))
