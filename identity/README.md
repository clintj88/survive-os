# SURVIVE OS Identity System

Central identity and access management for SURVIVE OS, built on LLDAP.

## Architecture

```
+------------------+     +------------------+     +------------------+
|  SURVIVE Module  | --> |  RBAC Middleware  | --> |      LLDAP       |
|  (FastAPI app)   |     |  (survive_rbac)   |     |  (LDAP + Web UI) |
+------------------+     +------------------+     +------------------+
                                                         |
                          +------------------+           |
                          |   SSSD Client    | ----------+
                          |  (PAM/NSS auth)  |
                          +------------------+
```

- **LLDAP** provides the LDAP directory with a lightweight web admin UI
- **RBAC Middleware** validates users and enforces role-based access in FastAPI services
- **SSSD** provides OS-level authentication (login, sudo) against LLDAP
- **Badge Provisioner** CLI manages user lifecycle

## Quick Start

### 1. Start LLDAP

```bash
cd identity/docker
cp .env.example .env
# Edit .env with secure passwords
docker compose up -d
```

### 2. Bootstrap Schema

```bash
cd identity/docker
./bootstrap-schema.sh
```

This creates custom attributes (role, team, badge_id) and default groups.

### 3. Create Users

```bash
cd identity/cli/badge-provisioner
pip install -e .

export LLDAP_URL=http://localhost:17170
export LLDAP_ADMIN_PASSWORD=your-password

badge-provisioner create \
    --username jdoe \
    --display-name "Jane Doe" \
    --email jane@survive.local \
    --role medic \
    --team medical
```

### 4. Set Up SSSD (on client machines)

```bash
cd identity/sssd
sudo ./install-sssd.sh --host lldap-server --password bind-password
```

### 5. Integrate RBAC in a Module

```python
from fastapi import Depends, FastAPI
from survive_rbac import init_auth, get_current_user, require_role, SurviveUser

app = FastAPI()

# Initialize at startup
init_auth("http://localhost:17170", "admin", "admin-password")

@app.get("/public")
async def public_endpoint(user: SurviveUser = Depends(get_current_user)):
    return {"hello": user.display_name}

@app.get("/admin-only")
async def admin_endpoint(user: SurviveUser = Depends(require_role("admin"))):
    return {"admin": True}

@app.get("/medical")
async def medical_endpoint(user: SurviveUser = Depends(require_role("medic", "admin"))):
    return {"access": "medical"}
```

## Custom User Schema

| Field        | Type   | Description                     |
|-------------|--------|---------------------------------|
| username    | string | Unique login ID (LDAP uid)      |
| display_name| string | Human-readable name             |
| email       | string | Email address                   |
| role        | string | Primary role (custom attribute) |
| team        | string | Team assignment (custom attr)   |
| badge_id    | string | Physical badge ID (custom attr) |
| created_at  | string | Account creation timestamp      |

## Default Groups/Roles

admin, medic, farmer, engineer, security, comms, governance, educator

## Components

| Directory               | Description                           |
|------------------------|---------------------------------------|
| `docker/`              | LLDAP Docker Compose and bootstrap    |
| `sssd/`                | SSSD/PAM/NSS client config templates  |
| `cli/badge-provisioner/`| User management CLI tool             |
| `middleware/`          | FastAPI RBAC middleware package        |
| `service/`             | Identity admin service (port 8001)    |

## Health Check

The identity admin service exposes `GET /health` on port 8001:

```json
{"status": "healthy", "version": "0.1.0"}
```

## Port

Identity admin: **8001**
