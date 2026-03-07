"""Role-based access control for the pharmacy module.

In production, authenticates against LLDAP via SSSD/PAM.
For development/testing, uses a simple header-based approach.
"""

from fastapi import Header, HTTPException


REQUIRED_ROLE = "medical"


def require_medical_role(x_user_role: str = Header(default="medical")) -> str:
    """Verify the user has the medical role.

    In production, SSSD/PAM handles authentication against LLDAP.
    The reverse proxy sets X-User-Role based on LDAP group membership.
    """
    if x_user_role != REQUIRED_ROLE:
        raise HTTPException(status_code=403, detail="Medical role required")
    return x_user_role
