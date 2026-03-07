"""SURVIVE OS example module - demonstrates the platform framework."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

MODULE_NAME = "example"
VERSION = "0.1.0"
CONFIG_PATH = Path(f"/etc/survive/{MODULE_NAME}.yml")
DATA_DIR = Path(f"/var/lib/survive/{MODULE_NAME}")


def load_config() -> dict[str, Any]:
    """Load module configuration from YAML file."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f) or {}
    return {}


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize database tables."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def get_db() -> sqlite3.Connection:
    """Get a connection to the module's SQLite database."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db_path = DATA_DIR / f"{MODULE_NAME}.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


config = load_config()
app = FastAPI(title=f"SURVIVE OS - {MODULE_NAME}", version=VERSION)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/health")
async def health() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({"status": "healthy", "version": VERSION})


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    """Serve the main UI page."""
    return HTMLResponse(
        (Path(__file__).parent / "static" / "index.html").read_text()
    )


@app.get("/api/notes")
async def list_notes() -> JSONResponse:
    """List all notes."""
    conn = get_db()
    rows = conn.execute("SELECT id, content, created_at FROM notes ORDER BY id DESC").fetchall()
    conn.close()
    return JSONResponse([dict(r) for r in rows])


@app.post("/api/notes")
async def create_note(body: dict[str, str]) -> JSONResponse:
    """Create a new note."""
    content = body.get("content", "").strip()
    if not content:
        return JSONResponse({"error": "content is required"}, status_code=400)
    conn = get_db()
    conn.execute("INSERT INTO notes (content) VALUES (?)", (content,))
    conn.commit()
    conn.close()
    return JSONResponse({"status": "created"}, status_code=201)
