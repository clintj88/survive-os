# SURVIVE OS - Project Instructions


## Project Overview
SURVIVE OS is a Debian-based operating system for
post-infrastructure communities. It provides offline-first
tools for communication, agriculture, medicine, governance,
security, and education on commodity hardware.


## Architecture
- Monorepo with independent modules per subsystem
- Each module is a systemd service with a local web UI
- Data stored in SQLite per module
- Shared data synced via CRDT (Automerge) engine
- All UIs served as local web apps (HTML/JS/CSS)
- Identity via LLDAP directory with SSSD clients
- Inter-module communication via Redis pub/sub
- Config in YAML at /etc/survive/[module].yml


## Tech Stack
- Backend: Python 3.11+ (FastAPI) or Node.js 20+
- Frontend: Preact + HTM (minimal bundle size)
- Database: SQLite3 (SQLCipher for encrypted modules)
- Sync: Automerge CRDTs over Protocol Buffers
- Maps: MapLibre GL JS + TileServer GL
- Hardware: Must run on Raspberry Pi 4 (4GB RAM)


## Coding Standards
- Python: Black formatter, type hints required, pytest
- JavaScript: ESLint, JSDoc comments, Vitest
- All modules must include: README.md, Dockerfile,
  systemd service file, health check endpoint
- API endpoints documented with OpenAPI 3.0 spec
- Error handling: Never crash. Log and degrade gracefully.
- Offline-first: NEVER require network for core function


## Module Integration Contract
Every module MUST:
1. Run as a systemd service
2. Serve UI on a designated port (see port map below)
3. Store data in /var/lib/survive/[module]/
4. Config at /etc/survive/[module].yml
5. Expose GET /health returning JSON {status, version}
6. Log to journald via systemd
7. Authenticate users against LLDAP via SSSD/PAM


## Port Map
- 8000: Platform shell (main UI)
- 8001: Identity admin
- 8010: Communication / BBS
- 8011: Communication / Ham Radio
- 8012: Communication / Meshtastic Gateway
- 8020: Security / Drone ops
- 8030: Agriculture
- 8040: Medical (encrypted)
- 8050: Resources / Inventory
- 8060: Maps
- 8070: Governance
- 8080: Weather
- 8090: Education / Knowledge base


## File Ownership Rules (Agent Teams)
Each team owns specific directories. Do NOT edit files
outside your team's directories without coordination:
- Platform Team: /platform, /shared
- Identity Team: /identity
- Sync Team: /sync
- Comms Team: /comms
- Security Team: /security
- Agriculture Team: /agriculture
- Medical Team: /medical
- Resources Team: /resources
- Maps Team: /maps
- Frontend Team: /frontend


## Git Conventions
- Branch: feature/[team]/[short-description]
- Commits: conventional commits (feat:, fix:, docs:)

