"""Skills registry for tracking tradeable services in the community."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/skills", tags=["skills"])

VALID_CATEGORIES = (
    "farming", "medical", "mechanical", "construction",
    "teaching", "cooking", "security", "crafting", "technology",
)

VALID_PROFICIENCY = ("beginner", "intermediate", "expert")


class SkillCreate(BaseModel):
    person_name: str
    skill_category: str
    skill_name: str
    proficiency: str = "beginner"
    hourly_rate: float = 1.0
    available: bool = True


class SkillUpdate(BaseModel):
    proficiency: Optional[str] = None
    hourly_rate: Optional[float] = None
    available: Optional[bool] = None


@router.get("")
def list_skills(
    category: Optional[str] = None,
    available: Optional[bool] = None,
    person: Optional[str] = None,
) -> list[dict]:
    conditions: list[str] = []
    params: list = []
    if category:
        conditions.append("skill_category = ?")
        params.append(category)
    if available is not None:
        conditions.append("available = ?")
        params.append(1 if available else 0)
    if person:
        conditions.append("person_name = ?")
        params.append(person)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return query(
        f"""SELECT id, person_name, skill_category, skill_name, proficiency,
                   hourly_rate, available, created_at, updated_at
            FROM skills {where}
            ORDER BY skill_category, skill_name""",
        tuple(params),
    )


@router.get("/categories")
def list_categories() -> list[str]:
    return list(VALID_CATEGORIES)


@router.get("/search")
def search_skills(q: str) -> list[dict]:
    """Search skills by name or person."""
    pattern = f"%{q}%"
    return query(
        """SELECT id, person_name, skill_category, skill_name, proficiency,
                  hourly_rate, available, created_at, updated_at
           FROM skills
           WHERE skill_name LIKE ? OR person_name LIKE ?
           ORDER BY skill_category, skill_name""",
        (pattern, pattern),
    )


@router.get("/{skill_id}")
def get_skill(skill_id: int) -> dict:
    results = query(
        """SELECT id, person_name, skill_category, skill_name, proficiency,
                  hourly_rate, available, created_at, updated_at
           FROM skills WHERE id = ?""",
        (skill_id,),
    )
    if not results:
        raise HTTPException(status_code=404, detail="Skill not found")
    return results[0]


@router.post("", status_code=201)
def create_skill(skill: SkillCreate) -> dict:
    if skill.skill_category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category: {skill.skill_category}. Must be one of: {', '.join(VALID_CATEGORIES)}",
        )
    if skill.proficiency not in VALID_PROFICIENCY:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid proficiency: {skill.proficiency}. Must be one of: {', '.join(VALID_PROFICIENCY)}",
        )
    skill_id = execute(
        """INSERT INTO skills (person_name, skill_category, skill_name, proficiency, hourly_rate, available)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (skill.person_name, skill.skill_category, skill.skill_name,
         skill.proficiency, skill.hourly_rate, 1 if skill.available else 0),
    )
    return get_skill(skill_id)


@router.put("/{skill_id}")
def update_skill(skill_id: int, update: SkillUpdate) -> dict:
    existing = query("SELECT id FROM skills WHERE id = ?", (skill_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Skill not found")

    updates: list[str] = []
    params: list = []
    if update.proficiency is not None:
        if update.proficiency not in VALID_PROFICIENCY:
            raise HTTPException(status_code=400, detail=f"Invalid proficiency: {update.proficiency}")
        updates.append("proficiency = ?")
        params.append(update.proficiency)
    if update.hourly_rate is not None:
        updates.append("hourly_rate = ?")
        params.append(update.hourly_rate)
    if update.available is not None:
        updates.append("available = ?")
        params.append(1 if update.available else 0)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.append(skill_id)
    execute(f"UPDATE skills SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_skill(skill_id)
