"""Historical data queries and CSV export."""

import csv
import io
from typing import Any, Optional

from .database import query


def query_readings(
    sensor_type: str,
    node_id: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    aggregation: Optional[str] = None,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    """Query historical sensor readings with optional aggregation."""
    table_map = {
        "soil": "soil_readings",
        "weather": "weather_readings",
        "rain": "rain_readings",
    }
    table = table_map.get(sensor_type)
    if not table:
        return []

    if aggregation in ("hourly", "daily"):
        return _aggregated_query(table, sensor_type, node_id, start, end, aggregation, limit)

    conditions: list[str] = []
    params: list[Any] = []
    if node_id:
        conditions.append("node_id = ?")
        params.append(node_id)
    if start:
        conditions.append("timestamp >= ?")
        params.append(start)
    if end:
        conditions.append("timestamp <= ?")
        params.append(end)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)
    return query(
        f"SELECT * FROM {table} {where} ORDER BY timestamp DESC LIMIT ?",
        tuple(params),
    )


def _aggregated_query(
    table: str,
    sensor_type: str,
    node_id: Optional[str],
    start: Optional[str],
    end: Optional[str],
    aggregation: str,
    limit: int,
) -> list[dict[str, Any]]:
    """Run time-bucketed aggregation queries."""
    if aggregation == "hourly":
        bucket = "strftime('%Y-%m-%dT%H:00:00', timestamp)"
    else:
        bucket = "strftime('%Y-%m-%d', timestamp)"

    agg_cols = _get_agg_columns(sensor_type)

    conditions: list[str] = []
    params: list[Any] = []
    if node_id:
        conditions.append("node_id = ?")
        params.append(node_id)
    if start:
        conditions.append("timestamp >= ?")
        params.append(start)
    if end:
        conditions.append("timestamp <= ?")
        params.append(end)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)

    return query(
        f"""SELECT {bucket} as period, node_id, {agg_cols}, COUNT(*) as reading_count
            FROM {table} {where}
            GROUP BY period, node_id
            ORDER BY period DESC
            LIMIT ?""",
        tuple(params),
    )


def _get_agg_columns(sensor_type: str) -> str:
    if sensor_type == "soil":
        return "AVG(moisture_pct) as avg_moisture_pct, AVG(temperature_c) as avg_temperature_c"
    elif sensor_type == "weather":
        return ("AVG(temperature_c) as avg_temperature_c, "
                "AVG(humidity_pct) as avg_humidity_pct, "
                "AVG(pressure_hpa) as avg_pressure_hpa, "
                "MIN(temperature_c) as min_temperature_c, "
                "MAX(temperature_c) as max_temperature_c")
    elif sensor_type == "rain":
        return "SUM(rainfall_mm) as total_rainfall_mm"
    return "*"


def export_csv(
    sensor_type: str,
    node_id: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> str:
    """Export readings as CSV string."""
    rows = query_readings(sensor_type, node_id, start, end, limit=100000)
    if not rows:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
