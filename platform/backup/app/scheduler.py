"""Backup scheduler configuration for systemd timers.

Generates systemd timer/service units for automated backups.
This module does NOT use cron — it uses systemd timers as specified.
"""

from pathlib import Path
from typing import Any

SERVICE_TEMPLATE = """[Unit]
Description=SURVIVE OS Backup - {description}
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 -m platform.backup.app.main --run-backup {args}
WorkingDirectory=/opt/survive-os
User=survive
Group=survive
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""

TIMER_TEMPLATE = """[Unit]
Description=SURVIVE OS Backup Timer - {description}

[Timer]
OnCalendar={schedule}
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
"""


def generate_service_unit(
    name: str,
    description: str,
    args: str = "",
) -> str:
    """Generate a systemd service unit file content."""
    return SERVICE_TEMPLATE.format(description=description, args=args).strip()


def generate_timer_unit(
    name: str,
    description: str,
    schedule: str = "*-*-* 02:00:00",
) -> str:
    """Generate a systemd timer unit file content.

    Default schedule: daily at 2:00 AM.
    """
    return TIMER_TEMPLATE.format(description=description, schedule=schedule).strip()


def write_systemd_units(
    service_dir: str,
    name: str = "survive-backup",
    description: str = "Daily database and blob backup",
    schedule: str = "*-*-* 02:00:00",
    args: str = "",
) -> dict[str, str]:
    """Write systemd service and timer unit files.

    Args:
        service_dir: Directory for unit files (e.g., /etc/systemd/system/).
        name: Service name prefix.
        description: Human-readable description.
        schedule: OnCalendar schedule expression.
        args: Additional CLI args for the backup command.

    Returns:
        Dict with paths to the written files.
    """
    base = Path(service_dir)
    base.mkdir(parents=True, exist_ok=True)

    service_path = base / f"{name}.service"
    timer_path = base / f"{name}.timer"

    service_path.write_text(generate_service_unit(name, description, args))
    timer_path.write_text(generate_timer_unit(name, description, schedule))

    return {
        "service": str(service_path),
        "timer": str(timer_path),
    }
