"""Chemistry Recipe Database API routes."""

import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/chemistry", tags=["chemistry"])


class RecipeCreate(BaseModel):
    name: str
    category: str
    ingredients: list[dict] = []
    procedure: list[str] = []
    safety_notes: str = ""
    yield_amount: str = ""
    difficulty: str = "medium"


def _parse_recipe(row: dict) -> dict:
    row["ingredients"] = json.loads(row["ingredients"])
    row["procedure"] = json.loads(row["procedure"])
    return row


@router.get("")
def list_recipes(category: Optional[str] = Query(None)) -> list[dict]:
    if category:
        rows = query("SELECT * FROM chemistry_recipes WHERE category = ? ORDER BY name", (category,))
    else:
        rows = query("SELECT * FROM chemistry_recipes ORDER BY name")
    return [_parse_recipe(r) for r in rows]


@router.post("", status_code=201)
def create_recipe(recipe: RecipeCreate) -> dict:
    recipe_id = execute(
        """INSERT INTO chemistry_recipes (name, category, ingredients, procedure, safety_notes, yield, difficulty)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            recipe.name, recipe.category,
            json.dumps(recipe.ingredients), json.dumps(recipe.procedure),
            recipe.safety_notes, recipe.yield_amount, recipe.difficulty,
        ),
    )
    rows = query("SELECT * FROM chemistry_recipes WHERE id = ?", (recipe_id,))
    return _parse_recipe(rows[0])


@router.get("/search")
def search_recipes(q: str = Query(..., min_length=1)) -> list[dict]:
    rows = query("SELECT * FROM chemistry_recipes ORDER BY name")
    results = []
    q_lower = q.lower()
    for row in rows:
        ingredients = json.loads(row["ingredients"])
        ingredient_names = " ".join(i.get("name", "") for i in ingredients).lower()
        if q_lower in row["name"].lower() or q_lower in ingredient_names:
            results.append(_parse_recipe(row))
    return results


@router.get("/{recipe_id}")
def get_recipe(recipe_id: int) -> dict:
    rows = query("SELECT * FROM chemistry_recipes WHERE id = ?", (recipe_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return _parse_recipe(rows[0])
