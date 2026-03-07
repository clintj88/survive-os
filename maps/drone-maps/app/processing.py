"""Orthomosaic processing job management router for the drone-maps module."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database import VALID_JOB_STATUSES, execute, query

router = APIRouter(prefix="/api/processing", tags=["processing"])


class JobCreate(BaseModel):
    survey_id: int


class JobUpdate(BaseModel):
    status: str | None = None
    output_path: str | None = None
    resolution: float | None = None
    file_size: int | None = None
    error_message: str | None = None


@router.get("")
def list_jobs(survey_id: int | None = None, status: str = "") -> list[dict]:
    sql = "SELECT * FROM processing_jobs WHERE 1=1"
    params: list = []
    if survey_id is not None:
        sql += " AND survey_id = ?"
        params.append(survey_id)
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY created_at DESC"
    return query(sql, tuple(params))


@router.get("/{job_id}")
def get_job(job_id: int) -> dict:
    rows = query("SELECT * FROM processing_jobs WHERE id = ?", (job_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Job not found")
    return rows[0]


@router.post("", status_code=201)
def create_job(body: JobCreate) -> dict:
    if not query("SELECT id FROM surveys WHERE id = ?", (body.survey_id,)):
        raise HTTPException(status_code=404, detail="Survey not found")
    row_id = execute(
        "INSERT INTO processing_jobs (survey_id) VALUES (?)",
        (body.survey_id,),
    )
    return query("SELECT * FROM processing_jobs WHERE id = ?", (row_id,))[0]


@router.put("/{job_id}")
def update_job(job_id: int, body: JobUpdate) -> dict:
    existing = query("SELECT * FROM processing_jobs WHERE id = ?", (job_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Job not found")
    if body.status is not None and body.status not in VALID_JOB_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_JOB_STATUSES}")

    updates: dict = {}
    for field in ("status", "output_path", "resolution", "file_size", "error_message"):
        val = getattr(body, field)
        if val is not None:
            updates[field] = val

    if "status" in updates:
        if updates["status"] == "processing":
            updates["started_at"] = "datetime('now')"
        elif updates["status"] in ("completed", "failed"):
            updates["completed_at"] = "datetime('now')"

    if not updates:
        return existing[0]

    set_parts = []
    params: list = []
    for k, v in updates.items():
        if v in ("datetime('now')",):
            set_parts.append(f"{k} = datetime('now')")
        else:
            set_parts.append(f"{k} = ?")
            params.append(v)
    params.append(job_id)
    execute(
        f"UPDATE processing_jobs SET {', '.join(set_parts)} WHERE id = ?",
        tuple(params),
    )
    return query("SELECT * FROM processing_jobs WHERE id = ?", (job_id,))[0]


@router.post("/{job_id}/run")
def run_job(job_id: int) -> dict:
    """Mock ODM processing - immediately marks job as completed."""
    rows = query("SELECT * FROM processing_jobs WHERE id = ?", (job_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Job not found")
    job = rows[0]
    if job["status"] not in ("pending",):
        raise HTTPException(status_code=400, detail="Job must be in pending status to run")
    execute(
        """UPDATE processing_jobs
           SET status = 'completed',
               started_at = datetime('now'),
               completed_at = datetime('now'),
               output_path = ?,
               resolution = 0.05,
               file_size = 104857600
           WHERE id = ?""",
        (f"/var/lib/survive/drone-maps/output/survey_{job['survey_id']}_ortho.tif", job_id),
    )
    return query("SELECT * FROM processing_jobs WHERE id = ?", (job_id,))[0]
