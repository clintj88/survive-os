"""Tests for timestamp utilities."""

from datetime import datetime, timezone

from shared.db.timestamps import parse_timestamp, to_iso, utcnow


def test_utcnow_format():
    ts = utcnow()
    assert ts.endswith("Z")
    assert "T" in ts
    # Should be parseable
    dt = parse_timestamp(ts)
    assert dt.tzinfo is not None


def test_parse_z_suffix():
    dt = parse_timestamp("2026-03-07T12:00:00.000000Z")
    assert dt.year == 2026
    assert dt.month == 3
    assert dt.tzinfo == timezone.utc


def test_parse_offset_suffix():
    dt = parse_timestamp("2026-03-07T12:00:00+00:00")
    assert dt.year == 2026
    assert dt.tzinfo is not None


def test_to_iso_naive():
    dt = datetime(2026, 1, 1, 0, 0, 0)
    result = to_iso(dt)
    assert result.endswith("Z")
    assert "2026-01-01" in result


def test_to_iso_aware():
    dt = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = to_iso(dt)
    assert "2026-01-01T12:00:00" in result
    assert result.endswith("Z")


def test_roundtrip():
    ts = utcnow()
    dt = parse_timestamp(ts)
    ts2 = to_iso(dt)
    assert ts == ts2
