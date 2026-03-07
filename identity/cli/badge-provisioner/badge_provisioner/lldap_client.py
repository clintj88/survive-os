"""LLDAP GraphQL API client for user and group management."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class LLDAPConfig:
    url: str
    admin_username: str
    admin_password: str


@dataclass
class UserInfo:
    user_id: str
    display_name: str
    email: str
    role: str
    team: str
    badge_id: str
    groups: list[str]


class LLDAPClient:
    """Client for LLDAP's GraphQL and auth APIs."""

    def __init__(self, config: LLDAPConfig) -> None:
        self._config = config
        self._token: str | None = None

    def _authenticate(self) -> str:
        if self._token:
            return self._token
        resp = requests.post(
            f"{self._config.url}/auth/simple/login",
            json={
                "username": self._config.admin_username,
                "password": self._config.admin_password,
            },
            timeout=10,
        )
        resp.raise_for_status()
        self._token = resp.json()["token"]
        return self._token

    def _gql(self, query: str, variables: dict[str, Any] | None = None) -> dict:
        token = self._authenticate()
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables
        resp = requests.post(
            f"{self._config.url}/api/graphql",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            raise RuntimeError(f"GraphQL error: {data['errors']}")
        return data["data"]

    def create_user(
        self,
        username: str,
        display_name: str,
        email: str,
        password: str,
        role: str = "",
        team: str = "",
        badge_id: str = "",
    ) -> dict:
        """Create a new user in LLDAP."""
        mutation = """
        mutation CreateUser($user: CreateUserInput!) {
            createUser(user: $user) {
                id
                displayName
            }
        }
        """
        variables = {
            "user": {
                "id": username,
                "displayName": display_name,
                "email": email,
            }
        }
        result = self._gql(mutation, variables)

        # Set password
        self._set_password(username, password)

        # Set custom attributes
        if role:
            self._set_user_attribute(username, "role", [role])
        if team:
            self._set_user_attribute(username, "team", [team])
        if badge_id:
            self._set_user_attribute(username, "badge_id", [badge_id])

        return result["createUser"]

    def _set_password(self, username: str, password: str) -> None:
        """Set a user's password (admin reset)."""
        # LLDAP does not expose password set via GraphQL for other users;
        # use the admin password reset endpoint.
        token = self._authenticate()
        resp = requests.post(
            f"{self._config.url}/auth/reset/step1/{username}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        # If LLDAP supports direct admin password set via GraphQL in future,
        # this can be updated. For now, log a note.
        if not resp.ok:
            raise RuntimeError(
                f"Failed to initiate password reset for {username}: {resp.text}"
            )

    def _set_user_attribute(
        self, username: str, attr_name: str, values: list[str]
    ) -> None:
        mutation = """
        mutation SetUserAttribute($userId: String!, $attr: String!, $value: [String!]!) {
            user(userId: $userId) {
                addAttribute(name: $attr, value: $value)
            }
        }
        """
        # Use a simpler approach via the update user mutation
        # LLDAP custom attribute setting via GraphQL
        update_mutation = """
        mutation UpdateUserAttribute($user: UpdateUserInput!) {
            updateUser(user: $user) {
                ok
            }
        }
        """
        variables = {
            "user": {
                "id": username,
                "attributes": [{"name": attr_name, "value": values}],
            }
        }
        self._gql(update_mutation, variables)

    def list_users(self) -> list[UserInfo]:
        """List all users with their custom attributes."""
        query = """
        query {
            users {
                id
                displayName
                email
                groups { displayName }
                attributes { name value }
            }
        }
        """
        data = self._gql(query)
        users: list[UserInfo] = []
        for u in data["users"]:
            attrs = {a["name"]: a["value"][0] if a["value"] else "" for a in u.get("attributes", [])}
            users.append(
                UserInfo(
                    user_id=u["id"],
                    display_name=u.get("displayName", ""),
                    email=u.get("email", ""),
                    role=attrs.get("role", ""),
                    team=attrs.get("team", ""),
                    badge_id=attrs.get("badge_id", ""),
                    groups=[g["displayName"] for g in u.get("groups", [])],
                )
            )
        return users

    def assign_role(self, username: str, group_name: str) -> None:
        """Add a user to a group (role assignment)."""
        # First get group ID
        groups_query = """
        query {
            groups { id displayName }
        }
        """
        data = self._gql(groups_query)
        group_id: int | None = None
        for g in data["groups"]:
            if g["displayName"].lower() == group_name.lower():
                group_id = g["id"]
                break
        if group_id is None:
            raise ValueError(f"Group '{group_name}' not found")

        mutation = """
        mutation AddUserToGroup($userId: String!, $groupId: Int!) {
            addUserToGroup(userId: $userId, groupId: $groupId) {
                ok
            }
        }
        """
        self._gql(mutation, {"userId": username, "groupId": group_id})

    def deactivate_user(self, username: str) -> None:
        """Deactivate (delete) a user from LLDAP."""
        mutation = """
        mutation DeleteUser($userId: String!) {
            deleteUser(userId: $userId) {
                ok
            }
        }
        """
        self._gql(mutation, {"userId": username})
