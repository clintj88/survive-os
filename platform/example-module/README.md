# SURVIVE OS - Example Module

A working example module demonstrating the SURVIVE OS platform framework. Provides a simple notes application with a web UI.

## Features

- FastAPI backend with health check endpoint
- SQLite data storage
- YAML config loading from `/etc/survive/example.yml`
- Simple web UI (Preact-free vanilla JS for demonstration)
- Systemd service file
- Docker support

## Running Locally

```bash
pip install -e ".[dev]"
uvicorn app:app --reload --port 8000
```

## API

- `GET /health` - Returns `{status, version}`
- `GET /` - Web UI
- `GET /api/notes` - List all notes
- `POST /api/notes` - Create a note (`{content: "..."}`)

## Deployment

```bash
# Systemd
sudo cp survive-example.service /etc/systemd/system/
sudo systemctl enable --now survive-example

# Docker
docker build -t survive-example .
docker run -p 8000:8000 survive-example
```
