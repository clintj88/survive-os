# SURVIVE OS - Platform Module Framework

Shared infrastructure and scaffolding for building SURVIVE OS modules.

## Contents

### `templates/survive-module.service`

Parameterized systemd unit file using systemd template instances (`%i`). Any module can be deployed by symlinking or copying this template:

```bash
sudo systemctl enable survive-module@agriculture.service
```

Features: automatic restart, journald logging, security hardening (ProtectSystem, NoNewPrivileges), Pi 4-friendly resource limits (512M RAM, 80% CPU).

### `nginx/survive-proxy.conf`

Nginx reverse proxy configuration routing all modules through a single entry point at `survive.local`:

| Path           | Port | Module              |
|----------------|------|---------------------|
| `/`            | 8000 | Platform shell      |
| `/identity/`   | 8001 | Identity admin      |
| `/comms/`      | 8010 | Communication / BBS |
| `/security/`   | 8020 | Security / Drone ops|
| `/agriculture/` | 8030 | Agriculture        |
| `/medical/`    | 8040 | Medical (encrypted) |
| `/resources/`  | 8050 | Resources/Inventory |
| `/maps/`       | 8060 | Maps                |
| `/governance/` | 8070 | Governance          |
| `/weather/`    | 8080 | Weather             |
| `/education/`  | 8090 | Education / KB      |

### `scaffolding/python/`

Template for Python (FastAPI) modules. Includes:

- `pyproject.toml` - Dependencies: fastapi, uvicorn, pyyaml
- `app.py` - FastAPI app with `/health` endpoint, config loader, SQLite helper
- `Dockerfile` - Production container with health check
- `README.md` - Module documentation template

Usage: Copy the directory, replace all `MODULE_NAME` placeholders with your module name.

### `scaffolding/node/`

Template for Node.js modules. Includes:

- `package.json` - Node 20+, js-yaml dependency
- `server.js` - HTTP server with `/health` endpoint and config loader
- `Dockerfile` - Production container with health check
- `README.md` - Module documentation template

Usage: Copy the directory, replace all `MODULE_NAME` placeholders with your module name.

### `example-module/`

A working FastAPI module demonstrating the framework. Simple notes app with:

- Health check at `GET /health`
- Web UI at `GET /`
- REST API (`GET/POST /api/notes`)
- Config loading from `/etc/survive/example.yml`
- SQLite storage at `/var/lib/survive/example/`
- Systemd service file and Dockerfile

Run it:

```bash
cd example-module
pip install -e ".[dev]"
uvicorn app:app --reload --port 8000
```

## Module Integration Contract

Every module MUST:

1. Run as a systemd service
2. Serve UI on its designated port
3. Store data in `/var/lib/survive/[module]/`
4. Load config from `/etc/survive/[module].yml`
5. Expose `GET /health` returning `{status, version}`
6. Log to journald via systemd
7. Authenticate against LLDAP via SSSD/PAM
