"""Identity admin service for SURVIVE OS - serves on port 8001."""

from __future__ import annotations

import os

from fastapi import FastAPI

app = FastAPI(title="SURVIVE OS Identity Admin", version="0.1.0")

SERVICE_VERSION = "0.1.0"


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "version": SERVICE_VERSION}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8001")))
