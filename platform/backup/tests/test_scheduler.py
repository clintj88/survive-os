"""Tests for systemd unit generation."""

from app.scheduler import (
    generate_service_unit,
    generate_timer_unit,
    write_systemd_units,
)


def test_generate_service_unit():
    unit = generate_service_unit("survive-backup", "Daily backup")
    assert "[Unit]" in unit
    assert "[Service]" in unit
    assert "Type=oneshot" in unit
    assert "Daily backup" in unit


def test_generate_timer_unit():
    unit = generate_timer_unit("survive-backup", "Daily backup", schedule="*-*-* 03:00:00")
    assert "[Timer]" in unit
    assert "OnCalendar=*-*-* 03:00:00" in unit
    assert "Persistent=true" in unit


def test_write_systemd_units(tmp_path):
    result = write_systemd_units(str(tmp_path))
    assert "service" in result
    assert "timer" in result
    from pathlib import Path
    assert Path(result["service"]).exists()
    assert Path(result["timer"]).exists()
