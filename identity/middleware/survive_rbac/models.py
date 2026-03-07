"""User models for SURVIVE OS RBAC."""

from __future__ import annotations

from pydantic import BaseModel


class SurviveUser(BaseModel):
    """Represents an authenticated SURVIVE OS user."""

    username: str
    display_name: str
    email: str
    role: str = ""
    team: str = ""
    badge_id: str = ""
    groups: list[str] = []

    def has_role(self, role: str) -> bool:
        """Check if user belongs to a role/group."""
        return role.lower() in [g.lower() for g in self.groups]

    def has_any_role(self, *roles: str) -> bool:
        """Check if user belongs to any of the given roles."""
        lower_groups = [g.lower() for g in self.groups]
        return any(r.lower() in lower_groups for r in roles)
