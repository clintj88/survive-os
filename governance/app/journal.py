"""Community Journal routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/journal", tags=["journal"])


class JournalEntryCreate(BaseModel):
    title: str
    content: str
    author: str
    entry_date: Optional[str] = None
    category: str = "daily_log"
    attachments: list[str] = []


@router.get("/entries")
def list_entries(
    category: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
) -> list[dict]:
    sql = "SELECT * FROM journal_entries WHERE 1=1"
    params: list = []
    if category:
        sql += " AND category = ?"
        params.append(category)
    if start_date:
        sql += " AND entry_date >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND entry_date <= ?"
        params.append(end_date)
    sql += " ORDER BY entry_date DESC, created_at DESC"
    return query(sql, tuple(params))


@router.get("/entries/{entry_id}")
def get_entry(entry_id: int) -> dict:
    results = query("SELECT * FROM journal_entries WHERE id = ?", (entry_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Entry not found")
    return results[0]


@router.post("/entries", status_code=201)
def create_entry(entry: JournalEntryCreate) -> dict:
    import json
    attachments_json = json.dumps(entry.attachments)
    if entry.entry_date:
        eid = execute(
            """INSERT INTO journal_entries (entry_date, title, content, author, category, attachments)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (entry.entry_date, entry.title, entry.content, entry.author, entry.category, attachments_json),
        )
    else:
        eid = execute(
            """INSERT INTO journal_entries (title, content, author, category, attachments)
               VALUES (?, ?, ?, ?, ?)""",
            (entry.title, entry.content, entry.author, entry.category, attachments_json),
        )
    return get_entry(eid)
