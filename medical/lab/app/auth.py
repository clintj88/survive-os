"""Role-based access middleware for the Lab module.

In production, authenticates against LLDAP via SSSD/PAM.
For development/testing, uses a simple header-based scheme.
"""

from fastapi import Header, HTTPException


async def require_medical_role(
    x_user: str = Header(default=""),
    x_role: str = Header(default=""),
) -> str:
    """Verify the request has medical role authorization.

    In production, SSSD/PAM handles authentication and the reverse proxy
    injects X-User and X-Role headers. Returns the authenticated username.
    """
    if not x_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    if x_role != "medical":
        raise HTTPException(status_code=403, detail="Medical role required")
    return x_user
