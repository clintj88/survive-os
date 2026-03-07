"""Image metadata management router for the drone-maps module."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/images", tags=["images"])


class ImageCreate(BaseModel):
    survey_id: int
    filename: str
    filepath: str = ""
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    captured_at: str | None = None


@router.get("")
def list_images(survey_id: int | None = None) -> list[dict]:
    if survey_id is not None:
        return query("SELECT * FROM images WHERE survey_id = ? ORDER BY created_at DESC", (survey_id,))
    return query("SELECT * FROM images ORDER BY created_at DESC")


@router.get("/{image_id}")
def get_image(image_id: int) -> dict:
    rows = query("SELECT * FROM images WHERE id = ?", (image_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Image not found")
    return rows[0]


@router.post("", status_code=201)
def create_image(body: ImageCreate) -> dict:
    if not query("SELECT id FROM surveys WHERE id = ?", (body.survey_id,)):
        raise HTTPException(status_code=404, detail="Survey not found")
    row_id = execute(
        """INSERT INTO images (survey_id, filename, filepath, latitude, longitude, altitude, captured_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (body.survey_id, body.filename, body.filepath, body.latitude,
         body.longitude, body.altitude, body.captured_at),
    )
    return query("SELECT * FROM images WHERE id = ?", (row_id,))[0]


@router.delete("/{image_id}")
def delete_image(image_id: int) -> dict:
    rows = query("SELECT * FROM images WHERE id = ?", (image_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Image not found")
    execute("DELETE FROM images WHERE id = ?", (image_id,))
    return {"detail": "Image deleted"}
