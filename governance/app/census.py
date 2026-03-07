"""Census & Population routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/census", tags=["census"])


class PersonCreate(BaseModel):
    name: str
    dob: Optional[str] = None
    sex: Optional[str] = None
    occupation: str = ""
    housing_assignment: str = ""
    arrival_date: Optional[str] = None


class PersonUpdate(BaseModel):
    name: Optional[str] = None
    dob: Optional[str] = None
    sex: Optional[str] = None
    occupation: Optional[str] = None
    housing_assignment: Optional[str] = None
    status: Optional[str] = None


class SkillAssessment(BaseModel):
    category: str
    rating: int


@router.get("/persons")
def list_persons(
    status: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
) -> list[dict]:
    sql = "SELECT * FROM persons WHERE 1=1"
    params: list = []
    if status:
        sql += " AND status = ?"
        params.append(status)
    if search:
        sql += " AND name LIKE ?"
        params.append(f"%{search}%")
    if skill:
        sql += " AND id IN (SELECT person_id FROM person_skills WHERE category = ?)"
        params.append(skill)
    sql += " ORDER BY name"
    return query(sql, tuple(params))


@router.get("/persons/{person_id}")
def get_person(person_id: int) -> dict:
    results = query("SELECT * FROM persons WHERE id = ?", (person_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Person not found")
    person = results[0]
    person["skills"] = query(
        "SELECT category, rating FROM person_skills WHERE person_id = ? ORDER BY category",
        (person_id,),
    )
    return person


@router.post("/persons", status_code=201)
def create_person(person: PersonCreate) -> dict:
    params = (
        person.name, person.dob, person.sex,
        person.occupation, person.housing_assignment,
        person.arrival_date,
    )
    if person.arrival_date:
        pid = execute(
            """INSERT INTO persons (name, dob, sex, occupation, housing_assignment, arrival_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            params,
        )
    else:
        pid = execute(
            """INSERT INTO persons (name, dob, sex, occupation, housing_assignment)
               VALUES (?, ?, ?, ?, ?)""",
            (person.name, person.dob, person.sex, person.occupation, person.housing_assignment),
        )
    return get_person(pid)


@router.put("/persons/{person_id}")
def update_person(person_id: int, person: PersonUpdate) -> dict:
    existing = query("SELECT id FROM persons WHERE id = ?", (person_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Person not found")
    updates: list[str] = []
    params: list = []
    for field in ("name", "dob", "sex", "occupation", "housing_assignment", "status"):
        val = getattr(person, field)
        if val is not None:
            updates.append(f"{field} = ?")
            params.append(val)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    params.append(person_id)
    execute(f"UPDATE persons SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_person(person_id)


@router.post("/persons/{person_id}/skills", status_code=201)
def set_skill(person_id: int, skill: SkillAssessment) -> dict:
    existing = query("SELECT id FROM persons WHERE id = ?", (person_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Person not found")
    execute(
        """INSERT INTO person_skills (person_id, category, rating)
           VALUES (?, ?, ?)
           ON CONFLICT(person_id, category) DO UPDATE SET rating = excluded.rating""",
        (person_id, skill.category, skill.rating),
    )
    return get_person(person_id)


@router.get("/stats")
def population_stats() -> dict:
    total = query("SELECT COUNT(*) as count FROM persons WHERE status = 'active'")[0]["count"]
    by_sex = query(
        "SELECT sex, COUNT(*) as count FROM persons WHERE status = 'active' GROUP BY sex"
    )
    by_status = query("SELECT status, COUNT(*) as count FROM persons GROUP BY status")
    skill_counts = query(
        """SELECT category, COUNT(*) as count, ROUND(AVG(rating), 1) as avg_rating
           FROM person_skills ps JOIN persons p ON ps.person_id = p.id
           WHERE p.status = 'active'
           GROUP BY category ORDER BY category"""
    )
    return {
        "total_active": total,
        "by_sex": by_sex,
        "by_status": by_status,
        "skills_summary": skill_counts,
    }
