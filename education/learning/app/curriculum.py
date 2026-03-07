"""Lesson Plans & Curriculum API routes."""

import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api", tags=["curriculum"])


class LessonCreate(BaseModel):
    title: str
    subject: str
    age_group: str = "adult"
    duration: str = ""
    objectives: list[str] = []
    materials_needed: list[str] = []
    procedure: list[str] = []
    assessment: str = ""


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    age_group: Optional[str] = None
    objectives: Optional[list[str]] = None
    procedure: Optional[list[str]] = None
    assessment: Optional[str] = None


class CurriculumCreate(BaseModel):
    subject: str
    grade_level: str = ""
    topic_sequence: list[str] = []
    recommended_resources: list[str] = []


def _parse_lesson(row: dict) -> dict:
    row["objectives"] = json.loads(row["objectives"])
    row["materials_needed"] = json.loads(row["materials_needed"])
    row["procedure"] = json.loads(row["procedure"])
    return row


def _parse_curriculum(row: dict) -> dict:
    row["topic_sequence"] = json.loads(row["topic_sequence"])
    row["recommended_resources"] = json.loads(row["recommended_resources"])
    return row


@router.get("/lessons")
def list_lessons(
    subject: Optional[str] = Query(None),
    age_group: Optional[str] = Query(None),
) -> list[dict]:
    conditions = []
    params: list = []
    if subject:
        conditions.append("subject = ?")
        params.append(subject)
    if age_group:
        conditions.append("age_group = ?")
        params.append(age_group)

    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = query(f"SELECT * FROM lesson_plans{where} ORDER BY title", tuple(params))
    return [_parse_lesson(r) for r in rows]


@router.post("/lessons", status_code=201)
def create_lesson(lesson: LessonCreate) -> dict:
    lesson_id = execute(
        """INSERT INTO lesson_plans (title, subject, age_group, duration, objectives, materials_needed, procedure, assessment)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            lesson.title, lesson.subject, lesson.age_group, lesson.duration,
            json.dumps(lesson.objectives), json.dumps(lesson.materials_needed),
            json.dumps(lesson.procedure), lesson.assessment,
        ),
    )
    rows = query("SELECT * FROM lesson_plans WHERE id = ?", (lesson_id,))
    return _parse_lesson(rows[0])


@router.get("/lessons/search")
def search_lessons(q: str = Query(..., min_length=1)) -> list[dict]:
    rows = query("SELECT * FROM lesson_plans ORDER BY title")
    q_lower = q.lower()
    results = []
    for row in rows:
        if q_lower in row["title"].lower() or q_lower in row["subject"].lower():
            results.append(_parse_lesson(row))
    return results


@router.get("/lessons/{lesson_id}")
def get_lesson(lesson_id: int) -> dict:
    rows = query("SELECT * FROM lesson_plans WHERE id = ?", (lesson_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return _parse_lesson(rows[0])


@router.put("/lessons/{lesson_id}")
def update_lesson(lesson_id: int, data: LessonUpdate) -> dict:
    existing = query("SELECT id FROM lesson_plans WHERE id = ?", (lesson_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Lesson not found")

    updates: list[str] = []
    params: list = []
    for field in ["title", "subject", "age_group", "assessment"]:
        value = getattr(data, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)
    if data.objectives is not None:
        updates.append("objectives = ?")
        params.append(json.dumps(data.objectives))
    if data.procedure is not None:
        updates.append("procedure = ?")
        params.append(json.dumps(data.procedure))

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(lesson_id)
    execute(f"UPDATE lesson_plans SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_lesson(lesson_id)


@router.get("/curricula")
def list_curricula() -> list[dict]:
    rows = query("SELECT * FROM curricula ORDER BY subject")
    return [_parse_curriculum(r) for r in rows]


@router.post("/curricula", status_code=201)
def create_curriculum(curr: CurriculumCreate) -> dict:
    curr_id = execute(
        "INSERT INTO curricula (subject, grade_level, topic_sequence, recommended_resources) VALUES (?, ?, ?, ?)",
        (curr.subject, curr.grade_level, json.dumps(curr.topic_sequence), json.dumps(curr.recommended_resources)),
    )
    rows = query("SELECT * FROM curricula WHERE id = ?", (curr_id,))
    return _parse_curriculum(rows[0])


@router.get("/curricula/{curriculum_id}")
def get_curriculum(curriculum_id: int) -> dict:
    rows = query("SELECT * FROM curricula WHERE id = ?", (curriculum_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Curriculum not found")
    return _parse_curriculum(rows[0])
