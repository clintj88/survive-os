"""Print job CRUD router."""

import json
import os
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .database import (
    VALID_DPI,
    VALID_ORIENTATIONS,
    VALID_PAPER_SIZES,
    execute,
    query,
)
from .renderer import render_map

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

_output_dir: str = "/var/lib/survive/print-maps/output"


def set_output_dir(path: str) -> None:
    global _output_dir
    _output_dir = path


class JobCreate(BaseModel):
    title: str = ""
    center_lat: float = Field(ge=-90, le=90)
    center_lng: float = Field(ge=-180, le=180)
    zoom: int = Field(default=13, ge=1, le=20)
    paper_size: str = "A4"
    paper_width_mm: float | None = None
    paper_height_mm: float | None = None
    orientation: str = "portrait"
    dpi: int = 300
    overlay_layers: list[str] = Field(default_factory=list)
    include_legend: bool = True
    include_scale_bar: bool = True
    include_north_arrow: bool = True
    include_grid: bool = False
    include_date: bool = True
    requested_by: str = ""


class JobUpdate(BaseModel):
    title: str | None = None
    status: str | None = None


@router.post("", status_code=201)
def create_job(body: JobCreate) -> dict:
    if body.paper_size not in VALID_PAPER_SIZES:
        raise HTTPException(400, f"Invalid paper_size. Must be one of: {VALID_PAPER_SIZES}")
    if body.orientation not in VALID_ORIENTATIONS:
        raise HTTPException(400, f"Invalid orientation. Must be one of: {VALID_ORIENTATIONS}")
    if body.dpi not in VALID_DPI:
        raise HTTPException(400, f"Invalid dpi. Must be one of: {VALID_DPI}")
    if body.paper_size == "custom" and (not body.paper_width_mm or not body.paper_height_mm):
        raise HTTPException(400, "Custom paper size requires paper_width_mm and paper_height_mm")

    layers_json = json.dumps(body.overlay_layers)
    job_id = execute(
        """INSERT INTO print_jobs
           (title, center_lat, center_lng, zoom, paper_size, paper_width_mm,
            paper_height_mm, orientation, dpi, overlay_layers,
            include_legend, include_scale_bar, include_north_arrow,
            include_grid, include_date, requested_by)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            body.title, body.center_lat, body.center_lng, body.zoom,
            body.paper_size, body.paper_width_mm, body.paper_height_mm,
            body.orientation, body.dpi, layers_json,
            int(body.include_legend), int(body.include_scale_bar),
            int(body.include_north_arrow), int(body.include_grid),
            int(body.include_date), body.requested_by,
        ),
    )

    # Run stub renderer immediately
    try:
        execute("UPDATE print_jobs SET status = 'rendering' WHERE id = ?", (job_id,))
        output_path = render_map(
            title=body.title,
            center_lat=body.center_lat,
            center_lng=body.center_lng,
            zoom=body.zoom,
            paper_size=body.paper_size,
            paper_width_mm=body.paper_width_mm,
            paper_height_mm=body.paper_height_mm,
            orientation=body.orientation,
            dpi=body.dpi,
            overlay_layers=body.overlay_layers,
            include_legend=body.include_legend,
            include_scale_bar=body.include_scale_bar,
            include_north_arrow=body.include_north_arrow,
            include_grid=body.include_grid,
            include_date=body.include_date,
            output_dir=_output_dir,
            job_id=job_id,
        )
        file_size = os.path.getsize(output_path)
        execute(
            """UPDATE print_jobs
               SET status = 'completed', output_path = ?, file_size = ?,
                   completed_at = datetime('now')
               WHERE id = ?""",
            (output_path, file_size, job_id),
        )
    except Exception as exc:
        execute(
            "UPDATE print_jobs SET status = 'failed', error_message = ? WHERE id = ?",
            (str(exc), job_id),
        )

    rows = query("SELECT * FROM print_jobs WHERE id = ?", (job_id,))
    return _format_job(rows[0])


@router.get("")
def list_jobs(
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    sql = "SELECT * FROM print_jobs WHERE 1=1"
    params: list = []
    if status:
        sql += " AND status = ?"
        params.append(status)
    if date_from:
        sql += " AND created_at >= ?"
        params.append(date_from)
    if date_to:
        sql += " AND created_at <= ?"
        params.append(date_to)
    sql += " ORDER BY created_at DESC"
    return [_format_job(r) for r in query(sql, tuple(params))]


@router.get("/{job_id}")
def get_job(job_id: int) -> dict:
    rows = query("SELECT * FROM print_jobs WHERE id = ?", (job_id,))
    if not rows:
        raise HTTPException(404, "Job not found")
    return _format_job(rows[0])


@router.delete("/{job_id}")
def delete_job(job_id: int) -> dict:
    rows = query("SELECT * FROM print_jobs WHERE id = ?", (job_id,))
    if not rows:
        raise HTTPException(404, "Job not found")
    # Remove output file if it exists
    if rows[0]["output_path"]:
        path = Path(rows[0]["output_path"])
        if path.exists():
            path.unlink()
    execute("DELETE FROM print_jobs WHERE id = ?", (job_id,))
    return {"deleted": job_id}


@router.get("/{job_id}/download")
def download_job(job_id: int) -> FileResponse:
    rows = query("SELECT * FROM print_jobs WHERE id = ?", (job_id,))
    if not rows:
        raise HTTPException(404, "Job not found")
    job = rows[0]
    if job["status"] != "completed" or not job["output_path"]:
        raise HTTPException(400, "Job output not available")
    path = Path(job["output_path"])
    if not path.exists():
        raise HTTPException(404, "Output file not found")
    filename = f"{job['title'] or 'map'}_{job_id}.png"
    return FileResponse(str(path), media_type="image/png", filename=filename)


def _format_job(row: dict) -> dict:
    job = dict(row)
    job["overlay_layers"] = json.loads(job.get("overlay_layers", "[]"))
    for field in (
        "include_legend", "include_scale_bar", "include_north_arrow",
        "include_grid", "include_date",
    ):
        job[field] = bool(job.get(field))
    return job
