"""FastAPI middleware and dependencies for LLDAP-backed RBAC."""

from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable

import requests
from fastapi import Depends, HTTPException, Request, status

from survive_rbac.models import SurviveUser

logger = logging.getLogger("survive_rbac")


class LDAPAuthBackend:
    """Validates user sessions against LLDAP and caches user info."""

    def __init__(self, lldap_url: str, admin_username: str, admin_password: str) -> None:
        self.lldap_url = lldap_url.rstrip("/")
        self.admin_username = admin_username
        self.admin_password = admin_password
        self._admin_token: str | None = None

    def _get_admin_token(self) -> str:
        if self._admin_token:
            return self._admin_token
        resp = requests.post(
            f"{self.lldap_url}/auth/simple/login",
            json={"username": self.admin_username, "password": self.admin_password},
            timeout=10,
        )
        resp.raise_for_status()
        self._admin_token = resp.json()["token"]
        return self._admin_token

    def authenticate(self, username: str, password: str) -> SurviveUser | None:
        """Authenticate a user against LLDAP and return user info."""
        # Verify credentials
        resp = requests.post(
            f"{self.lldap_url}/auth/simple/login",
            json={"username": username, "password": password},
            timeout=10,
        )
        if not resp.ok:
            return None

        # Fetch user details with admin token
        return self.get_user(username)

    def get_user(self, username: str) -> SurviveUser | None:
        """Fetch user details from LLDAP by username."""
        token = self._get_admin_token()
        query = """
        query GetUser($userId: String!) {
            user(userId: $userId) {
                id
                displayName
                email
                groups { displayName }
                attributes { name value }
            }
        }
        """
        resp = requests.post(
            f"{self.lldap_url}/api/graphql",
            json={"query": query, "variables": {"userId": username}},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if not resp.ok:
            logger.warning("Failed to fetch user %s: %s", username, resp.status_code)
            return None

        data = resp.json()
        if "errors" in data:
            logger.warning("GraphQL error fetching user %s: %s", username, data["errors"])
            return None

        u = data["data"]["user"]
        attrs = {a["name"]: a["value"][0] if a["value"] else "" for a in u.get("attributes", [])}
        return SurviveUser(
            username=u["id"],
            display_name=u.get("displayName", ""),
            email=u.get("email", ""),
            role=attrs.get("role", ""),
            team=attrs.get("team", ""),
            badge_id=attrs.get("badge_id", ""),
            groups=[g["displayName"] for g in u.get("groups", [])],
        )


# Global auth backend instance - initialized by the app
_auth_backend: LDAPAuthBackend | None = None


def init_auth(lldap_url: str, admin_username: str, admin_password: str) -> LDAPAuthBackend:
    """Initialize the global auth backend. Call once at app startup."""
    global _auth_backend
    _auth_backend = LDAPAuthBackend(lldap_url, admin_username, admin_password)
    return _auth_backend


async def get_current_user(request: Request) -> SurviveUser:
    """FastAPI dependency that extracts and validates the current user.

    Expects a session cookie or X-Username header (for service-to-service).
    """
    if _auth_backend is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth backend not initialized",
        )

    # Check for username in session or header
    username = request.headers.get("X-Survive-Username")
    if not username:
        session = request.cookies.get("survive_session")
        if session:
            # In production, decode a signed session token here
            username = session

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    user = _auth_backend.get_user(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


def require_role(*roles: str) -> Callable:
    """FastAPI dependency that requires the user to have one of the specified roles.

    Usage:
        @app.get("/admin", dependencies=[Depends(require_role("admin"))])
        async def admin_endpoint():
            ...

        # Or with user injection:
        @app.get("/medical")
        async def medical_endpoint(user: SurviveUser = Depends(require_role("medic", "admin"))):
            ...
    """

    async def role_checker(user: SurviveUser = Depends(get_current_user)) -> SurviveUser:
        if not user.has_any_role(*roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(roles)}",
            )
        return user

    return role_checker
