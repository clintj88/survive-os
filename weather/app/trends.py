"""Seasonal trend tracking and long-term data aggregation."""

from datetime import datetime, timezone
from typing import Any, Optional

from .database import query


def get_monthly_averages(year: Optional[int] = None) -> list[dict]:
    """Get monthly averages, optionally filtered by year."""
    year_filter = ""
    params: tuple = ()
    if year:
        year_filter = "AND strftime('%Y', observed_at) = ?"
        params = (str(year),)

    return query(
        f"""SELECT
            strftime('%Y', observed_at) as year,
            CAST(strftime('%m', observed_at) AS INTEGER) as month,
            ROUND(AVG(temperature_c), 1) as avg_temp_c,
            ROUND(MIN(temperature_c), 1) as min_temp_c,
            ROUND(MAX(temperature_c), 1) as max_temp_c,
            ROUND(AVG(humidity_pct), 1) as avg_humidity_pct,
            ROUND(AVG(pressure_hpa), 1) as avg_pressure_hpa,
            ROUND(SUM(COALESCE(rainfall_mm, 0)), 1) as total_rainfall_mm,
            COUNT(*) as observation_count
           FROM observations
           WHERE temperature_c IS NOT NULL {year_filter}
           GROUP BY strftime('%Y', observed_at), strftime('%m', observed_at)
           ORDER BY year, month""",
        params,
    )


def get_seasonal_averages(year: Optional[int] = None) -> list[dict]:
    """Get seasonal averages (DJF=Winter, MAM=Spring, JJA=Summer, SON=Fall)."""
    year_filter = ""
    params: tuple = ()
    if year:
        year_filter = "AND strftime('%Y', observed_at) = ?"
        params = (str(year),)

    return query(
        f"""SELECT
            strftime('%Y', observed_at) as year,
            CASE
                WHEN CAST(strftime('%m', observed_at) AS INTEGER) IN (12, 1, 2) THEN 'Winter'
                WHEN CAST(strftime('%m', observed_at) AS INTEGER) IN (3, 4, 5) THEN 'Spring'
                WHEN CAST(strftime('%m', observed_at) AS INTEGER) IN (6, 7, 8) THEN 'Summer'
                ELSE 'Fall'
            END as season,
            ROUND(AVG(temperature_c), 1) as avg_temp_c,
            ROUND(MIN(temperature_c), 1) as min_temp_c,
            ROUND(MAX(temperature_c), 1) as max_temp_c,
            ROUND(AVG(humidity_pct), 1) as avg_humidity_pct,
            ROUND(SUM(COALESCE(rainfall_mm, 0)), 1) as total_rainfall_mm,
            COUNT(*) as observation_count
           FROM observations
           WHERE temperature_c IS NOT NULL {year_filter}
           GROUP BY strftime('%Y', observed_at),
                CASE
                    WHEN CAST(strftime('%m', observed_at) AS INTEGER) IN (12, 1, 2) THEN 'Winter'
                    WHEN CAST(strftime('%m', observed_at) AS INTEGER) IN (3, 4, 5) THEN 'Spring'
                    WHEN CAST(strftime('%m', observed_at) AS INTEGER) IN (6, 7, 8) THEN 'Summer'
                    ELSE 'Fall'
                END
           ORDER BY year, season""",
        params,
    )


def get_annual_summary(year: Optional[int] = None) -> list[dict]:
    """Get annual summary statistics."""
    year_filter = ""
    params: tuple = ()
    if year:
        year_filter = "WHERE strftime('%Y', observed_at) = ?"
        params = (str(year),)

    return query(
        f"""SELECT
            strftime('%Y', observed_at) as year,
            ROUND(AVG(temperature_c), 1) as avg_temp_c,
            ROUND(MIN(temperature_c), 1) as min_temp_c,
            ROUND(MAX(temperature_c), 1) as max_temp_c,
            ROUND(AVG(humidity_pct), 1) as avg_humidity_pct,
            ROUND(AVG(pressure_hpa), 1) as avg_pressure_hpa,
            ROUND(SUM(COALESCE(rainfall_mm, 0)), 1) as total_rainfall_mm,
            COUNT(*) as observation_count
           FROM observations
           {year_filter}
           GROUP BY strftime('%Y', observed_at)
           ORDER BY year""",
        params,
    )


def get_year_over_year(month: int) -> list[dict]:
    """Compare a specific month across years."""
    return query(
        """SELECT
            strftime('%Y', observed_at) as year,
            ROUND(AVG(temperature_c), 1) as avg_temp_c,
            ROUND(MIN(temperature_c), 1) as min_temp_c,
            ROUND(MAX(temperature_c), 1) as max_temp_c,
            ROUND(AVG(humidity_pct), 1) as avg_humidity_pct,
            ROUND(SUM(COALESCE(rainfall_mm, 0)), 1) as total_rainfall_mm,
            COUNT(*) as observation_count
           FROM observations
           WHERE CAST(strftime('%m', observed_at) AS INTEGER) = ?
             AND temperature_c IS NOT NULL
           GROUP BY strftime('%Y', observed_at)
           ORDER BY year""",
        (month,),
    )


def get_growing_degree_days(
    base_temp_c: float = 10.0,
    year: Optional[int] = None,
) -> dict[str, Any]:
    """Calculate growing degree days (GDD) for a year.

    GDD = max(0, avg_daily_temp - base_temp).
    """
    target_year = year or datetime.now(timezone.utc).year

    daily = query(
        """SELECT
            DATE(observed_at) as day,
            AVG(temperature_c) as avg_temp
           FROM observations
           WHERE temperature_c IS NOT NULL
             AND strftime('%Y', observed_at) = ?
           GROUP BY DATE(observed_at)
           ORDER BY day""",
        (str(target_year),),
    )

    total_gdd = 0.0
    daily_gdd: list[dict[str, Any]] = []
    for row in daily:
        avg = row["avg_temp"] or 0
        gdd = max(0, avg - base_temp_c)
        total_gdd += gdd
        daily_gdd.append({
            "date": row["day"],
            "avg_temp_c": round(avg, 1),
            "gdd": round(gdd, 1),
            "cumulative_gdd": round(total_gdd, 1),
        })

    return {
        "year": target_year,
        "base_temp_c": base_temp_c,
        "total_gdd": round(total_gdd, 1),
        "days_with_data": len(daily_gdd),
        "daily": daily_gdd,
    }


def get_rainfall_by_season(year: Optional[int] = None) -> list[dict]:
    """Get rainfall totals grouped by season."""
    year_filter = ""
    params: tuple = ()
    if year:
        year_filter = "AND strftime('%Y', observed_at) = ?"
        params = (str(year),)

    return query(
        f"""SELECT
            strftime('%Y', observed_at) as year,
            CASE
                WHEN CAST(strftime('%m', observed_at) AS INTEGER) IN (12, 1, 2) THEN 'Winter'
                WHEN CAST(strftime('%m', observed_at) AS INTEGER) IN (3, 4, 5) THEN 'Spring'
                WHEN CAST(strftime('%m', observed_at) AS INTEGER) IN (6, 7, 8) THEN 'Summer'
                ELSE 'Fall'
            END as season,
            ROUND(SUM(COALESCE(rainfall_mm, 0)), 1) as total_rainfall_mm,
            COUNT(*) as observation_count
           FROM observations
           WHERE 1=1 {year_filter}
           GROUP BY strftime('%Y', observed_at),
                CASE
                    WHEN CAST(strftime('%m', observed_at) AS INTEGER) IN (12, 1, 2) THEN 'Winter'
                    WHEN CAST(strftime('%m', observed_at) AS INTEGER) IN (3, 4, 5) THEN 'Spring'
                    WHEN CAST(strftime('%m', observed_at) AS INTEGER) IN (6, 7, 8) THEN 'Summer'
                    ELSE 'Fall'
                END
           ORDER BY year, season""",
        params,
    )
