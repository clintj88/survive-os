"""Badge Provisioner CLI - Manage SURVIVE OS users via LLDAP."""

from __future__ import annotations

import os
import sys
import uuid

import click
from tabulate import tabulate

from badge_provisioner.lldap_client import LLDAPClient, LLDAPConfig


def _get_client() -> LLDAPClient:
    url = os.environ.get("LLDAP_URL", "http://localhost:17170")
    username = os.environ.get("LLDAP_ADMIN_USERNAME", "admin")
    password = os.environ.get("LLDAP_ADMIN_PASSWORD", "")
    if not password:
        click.echo("ERROR: LLDAP_ADMIN_PASSWORD environment variable is required.", err=True)
        sys.exit(1)
    return LLDAPClient(LLDAPConfig(url=url, admin_username=username, admin_password=password))


@click.group()
def main() -> None:
    """SURVIVE OS Badge Provisioner - Manage users in LLDAP."""


@main.command()
@click.option("--username", required=True, help="Unique username")
@click.option("--display-name", required=True, help="Display name")
@click.option("--email", required=True, help="Email address")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="User password")
@click.option("--role", default="", help="Role (e.g., medic, farmer, admin)")
@click.option("--team", default="", help="Team assignment")
@click.option("--badge-id", default="", help="Badge ID (auto-generated if empty)")
def create(
    username: str,
    display_name: str,
    email: str,
    password: str,
    role: str,
    team: str,
    badge_id: str,
) -> None:
    """Create a new user with a badge ID."""
    if not badge_id:
        badge_id = f"SRV-{uuid.uuid4().hex[:8].upper()}"
    client = _get_client()
    try:
        result = client.create_user(
            username=username,
            display_name=display_name,
            email=email,
            password=password,
            role=role,
            team=team,
            badge_id=badge_id,
        )
        click.echo(f"User '{username}' created with badge ID: {badge_id}")
    except Exception as e:
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)


@main.command(name="list")
def list_users() -> None:
    """List all users."""
    client = _get_client()
    try:
        users = client.list_users()
        if not users:
            click.echo("No users found.")
            return
        table = [
            [u.user_id, u.display_name, u.email, u.role, u.team, u.badge_id, ", ".join(u.groups)]
            for u in users
        ]
        click.echo(
            tabulate(table, headers=["Username", "Name", "Email", "Role", "Team", "Badge ID", "Groups"])
        )
    except Exception as e:
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--username", required=True, help="Username to assign role to")
@click.option("--group", required=True, help="Group/role name to assign")
def assign_role(username: str, group: str) -> None:
    """Assign a role (group) to a user."""
    client = _get_client()
    try:
        client.assign_role(username, group)
        click.echo(f"Assigned role '{group}' to user '{username}'.")
    except Exception as e:
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--username", required=True, help="Username to deactivate")
@click.confirmation_option(prompt="Are you sure you want to deactivate this user?")
def deactivate(username: str) -> None:
    """Deactivate (remove) a user."""
    client = _get_client()
    try:
        client.deactivate_user(username)
        click.echo(f"User '{username}' has been deactivated.")
    except Exception as e:
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)
