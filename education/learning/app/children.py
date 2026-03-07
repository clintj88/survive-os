"""Children's Education API routes."""

import json
import random
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/children", tags=["children"])


class MathSubmission(BaseModel):
    child_name: str
    exercise_type: str
    difficulty: int
    answers: list[dict]


class ReadingSubmission(BaseModel):
    child_name: str
    difficulty: int
    answers: list[dict]


@router.get("/math")
def generate_math(
    type: str = Query("addition"),
    difficulty: int = Query(1, ge=1, le=5),
    count: int = Query(5, ge=1, le=20),
) -> list[dict]:
    problems = []
    for _ in range(count):
        a, b, question, answer = _make_problem(type, difficulty)
        problems.append({"question": question, "answer": answer})
    return problems


def _make_problem(prob_type: str, difficulty: int) -> tuple:
    max_val = difficulty * 10
    if prob_type == "addition":
        a = random.randint(1, max_val)
        b = random.randint(1, max_val)
        return a, b, f"{a} + {b}", a + b
    elif prob_type == "subtraction":
        a = random.randint(1, max_val)
        b = random.randint(1, a)
        return a, b, f"{a} - {b}", a - b
    elif prob_type == "multiplication":
        a = random.randint(1, min(max_val, 12))
        b = random.randint(1, min(max_val, 12))
        return a, b, f"{a} x {b}", a * b
    elif prob_type == "division":
        b = random.randint(1, min(max_val, 12))
        answer = random.randint(1, min(max_val, 12))
        a = b * answer
        return a, b, f"{a} / {b}", answer
    else:
        a = random.randint(1, max_val)
        b = random.randint(1, max_val)
        return a, b, f"{a} + {b}", a + b


@router.post("/math/submit")
def submit_math(submission: MathSubmission) -> dict:
    correct = sum(1 for a in submission.answers if a.get("user_answer") == a.get("correct_answer"))
    total = len(submission.answers)

    execute(
        "INSERT INTO children_progress (child_name, exercise_type, difficulty, score, total) VALUES (?, ?, ?, ?, ?)",
        (submission.child_name, submission.exercise_type, submission.difficulty, correct, total),
    )

    return {"child_name": submission.child_name, "score": correct, "total": total, "percentage": round(correct / total * 100) if total else 0}


@router.get("/reading")
def get_reading(difficulty: int = Query(1, ge=1, le=5)) -> list[dict]:
    rows = query("SELECT * FROM reading_passages WHERE difficulty = ? ORDER BY id", (difficulty,))
    for row in rows:
        row["questions"] = json.loads(row["questions"])
    return rows


@router.post("/reading/submit")
def submit_reading(submission: ReadingSubmission) -> dict:
    correct = sum(1 for a in submission.answers if a.get("correct", False))
    total = len(submission.answers)

    execute(
        "INSERT INTO children_progress (child_name, exercise_type, difficulty, score, total) VALUES (?, ?, ?, ?, ?)",
        (submission.child_name, "reading", submission.difficulty, correct, total),
    )

    return {"child_name": submission.child_name, "score": correct, "total": total}


@router.get("/science")
def list_science(difficulty: Optional[int] = Query(None)) -> list[dict]:
    if difficulty is not None:
        rows = query("SELECT * FROM science_activities WHERE difficulty = ? ORDER BY title", (difficulty,))
    else:
        rows = query("SELECT * FROM science_activities ORDER BY difficulty, title")
    for row in rows:
        row["materials"] = json.loads(row["materials"])
        row["steps"] = json.loads(row["steps"])
    return rows


@router.get("/progress")
def get_progress(child_name: str = Query(..., min_length=1)) -> list[dict]:
    return query(
        "SELECT * FROM children_progress WHERE child_name = ? ORDER BY completed_at DESC",
        (child_name,),
    )
