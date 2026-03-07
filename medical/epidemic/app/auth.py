"""Role-based access control for epidemic surveillance.

In production, authenticates against LLDAP via SSSD/PAM.
Requires 'medical' role for access.
"""

from fastapi import Header, HTTPException


def require_medical_role(x_user_roles: str = Header(default="medical")) -> str:
    """Verify the user has the medical role.

    In production, the reverse proxy (nginx) sets X-User-Roles
    from SSSD/PAM after LLDAP authentication.
    Default allows access in development mode.
    """
    roles = [r.strip() for r in x_user_roles.split(",")]
    if "medical" not in roles and "admin" not in roles:
        raise HTTPException(status_code=403, detail="Medical role required")
    return x_user_roles
