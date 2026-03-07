# SURVIVE OS - Platform Shell

Main web UI shell for SURVIVE OS. Serves the platform interface on port 8000 and provides navigation to all subsystem modules.

## Architecture

- **Preact + HTM** - Lightweight UI with tagged template literals (no JSX transpilation)
- **ES modules via CDN** - No build step required; imports from esm.sh
- **Node.js static server** - Minimal HTTP server with health check and auth API
- **iframe module routing** - Each module runs independently; the shell embeds them

## Setup

```bash
cd frontend
npm install
npm start
```

The shell will be available at `http://localhost:8000`.

## Development

No build step is needed. Edit files in `src/` and reload the browser.

```bash
npm run dev    # Start dev server
npm test       # Run tests
npm run lint   # Lint source
```

## Project Structure

```
frontend/
  server.js              # Static file server + auth API (port 8000)
  public/
    index.html           # Entry point
  src/
    app.js               # Root Preact component
    lib.js               # Preact + HTM imports
    modules.js           # Module registry (port map)
    components/
      header.js          # Top bar with user/logout
      sidebar.js         # Navigation sidebar with health indicators
    pages/
      login.js           # Login page (LLDAP auth)
    styles/
      theme.css          # Design system (CSS variables, base styles)
      shell.css          # App shell layout styles
  survive-shell.service  # systemd unit file
  Dockerfile             # Container build
```

## Health Check

```
GET /health
→ {"status":"ok","version":"0.1.0"}
```

## Authentication

The shell authenticates users against LLDAP. In development, any non-empty credentials are accepted. Configure `LLDAP_HOST` and `LLDAP_PORT` environment variables for production.

## Design System

Dark theme with military/survival aesthetic. Key CSS variables:

- `--accent-green`: Primary action color (#3fb950)
- `--accent-amber`: Warning/caution (#d29922)
- `--accent-red`: Danger/error (#f85149)
- `--bg-primary`: Main background (#0d1117)

All colors meet WCAG AA contrast requirements against their respective backgrounds.
