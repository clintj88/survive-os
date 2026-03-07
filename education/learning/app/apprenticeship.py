"""Apprenticeship Tracking API routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api", tags=["apprenticeship"])


class ApprenticeCreate(BaseModel):
    person_name: str
    trade: str
    mentor_name: str = ""
    start_date: Optional[str] = None
    status: str = "active"


class ApprenticeUpdate(BaseModel):
    person_name: Optional[str] = None
    mentor_name: Optional[str] = None
    status: Optional[str] = None


class SkillUpdate(BaseModel):
    status: str
    certified_by: Optional[str] = None


class SkillChecklistCreate(BaseModel):
    trade: str
    skill_name: str
    sort_order: int = 0


@router.get("/apprentices")
def list_apprentices(
    trade: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
) -> list[dict]:
    conditions = []
    params: list = []
    if trade:
        conditions.append("trade = ?")
        params.append(trade)
    if status:
        conditions.append("status = ?")
        params.append(status)

    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    return query(f"SELECT * FROM apprentices{where} ORDER BY person_name", tuple(params))


@router.post("/apprentices", status_code=201)
def create_apprentice(apprentice: ApprenticeCreate) -> dict:
    params = [apprentice.person_name, apprentice.trade, apprentice.mentor_name]
    if apprentice.start_date:
        apprentice_id = execute(
            "INSERT INTO apprentices (person_name, trade, mentor_name, start_date, status) VALUES (?, ?, ?, ?, ?)",
            (apprentice.person_name, apprentice.trade, apprentice.mentor_name, apprentice.start_date, apprentice.status),
        )
    else:
        apprentice_id = execute(
            "INSERT INTO apprentices (person_name, trade, mentor_name, status) VALUES (?, ?, ?, ?)",
            (apprentice.person_name, apprentice.trade, apprentice.mentor_name, apprentice.status),
        )

    # Auto-create skill entries from checklists
    skills = query("SELECT id FROM skill_checklists WHERE trade = ?", (apprentice.trade,))
    for skill in skills:
        execute(
            "INSERT INTO apprentice_skills (apprentice_id, skill_id) VALUES (?, ?)",
            (apprentice_id, skill["id"]),
        )

    return _get_apprentice_detail(apprentice_id)


@router.get("/apprentices/{apprentice_id}")
def get_apprentice(apprentice_id: int) -> dict:
    return _get_apprentice_detail(apprentice_id)


def _get_apprentice_detail(apprentice_id: int) -> dict:
    rows = query("SELECT * FROM apprentices WHERE id = ?", (apprentice_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Apprentice not found")

    apprentice = rows[0]
    skills = query(
        """SELECT a_s.id, a_s.skill_id, s.skill_name, a_s.status, a_s.certified_date, a_s.certified_by
           FROM apprentice_skills a_s
           JOIN skill_checklists s ON a_s.skill_id = s.id
           WHERE a_s.apprentice_id = ?
           ORDER BY s.sort_order""",
        (apprentice_id,),
    )

    total = len(skills)
    completed = sum(1 for s in skills if s["status"] in ("demonstrated", "certified"))
    progress = round((completed / total * 100) if total > 0 else 0, 1)

    apprentice["skills"] = skills
    apprentice["progress_pct"] = progress
    return apprentice


@router.put("/apprentices/{apprentice_id}")
def update_apprentice(apprentice_id: int, data: ApprenticeUpdate) -> dict:
    existing = query("SELECT id FROM apprentices WHERE id = ?", (apprentice_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Apprentice not found")

    updates: list[str] = []
    params: list = []
    for field in ["person_name", "mentor_name", "status"]:
        value = getattr(data, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(apprentice_id)
    execute(f"UPDATE apprentices SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return _get_apprentice_detail(apprentice_id)


@router.put("/apprentices/{apprentice_id}/skills/{skill_id}")
def update_skill_status(apprentice_id: int, skill_id: int, data: SkillUpdate) -> dict:
    existing = query(
        "SELECT id FROM apprentice_skills WHERE apprentice_id = ? AND skill_id = ?",
        (apprentice_id, skill_id),
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Skill record not found")

    if data.status == "certified" and data.certified_by:
        from datetime import date
        execute(
            "UPDATE apprentice_skills SET status = ?, certified_date = ?, certified_by = ? WHERE apprentice_id = ? AND skill_id = ?",
            (data.status, date.today().isoformat(), data.certified_by, apprentice_id, skill_id),
        )
    else:
        execute(
            "UPDATE apprentice_skills SET status = ? WHERE apprentice_id = ? AND skill_id = ?",
            (data.status, apprentice_id, skill_id),
        )

    return _get_apprentice_detail(apprentice_id)


@router.get("/apprentices/{apprentice_id}/certificate")
def get_certificate(apprentice_id: int) -> dict:
    detail = _get_apprentice_detail(apprentice_id)
    if detail["progress_pct"] < 100:
        raise HTTPException(status_code=400, detail="Apprenticeship not yet completed")
    return {
        "person_name": detail["person_name"],
        "trade": detail["trade"],
        "mentor_name": detail["mentor_name"],
        "start_date": detail["start_date"],
        "skills_completed": len(detail["skills"]),
        "status": "certified",
    }


@router.get("/skill-checklists")
def list_skill_checklists() -> dict:
    rows = query("SELECT * FROM skill_checklists ORDER BY trade, sort_order")
    grouped: dict[str, list] = {}
    for row in rows:
        grouped.setdefault(row["trade"], []).append(row)
    return grouped


@router.post("/skill-checklists", status_code=201)
def create_skill_checklist(data: SkillChecklistCreate) -> dict:
    skill_id = execute(
        "INSERT INTO skill_checklists (trade, skill_name, sort_order) VALUES (?, ?, ?)",
        (data.trade, data.skill_name, data.sort_order),
    )
    rows = query("SELECT * FROM skill_checklists WHERE id = ?", (skill_id,))
    return rows[0]
