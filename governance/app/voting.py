"""Community Voting routes."""

import json
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/voting", tags=["voting"])


class BallotCreate(BaseModel):
    title: str
    description: str = ""
    ballot_type: str = "yes_no"
    options: list[str] = ["yes", "no"]
    voting_period_start: Optional[str] = None
    voting_period_end: str = ""
    created_by: str = ""


class VoteCast(BaseModel):
    voter_id: int
    choice: str


@router.get("/ballots")
def list_ballots() -> list[dict]:
    return query("SELECT * FROM ballots ORDER BY created_at DESC")


@router.get("/ballots/{ballot_id}")
def get_ballot(ballot_id: int) -> dict:
    results = query("SELECT * FROM ballots WHERE id = ?", (ballot_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Ballot not found")
    ballot = results[0]
    ballot["options"] = json.loads(ballot["options"])
    return ballot


@router.post("/ballots", status_code=201)
def create_ballot(ballot: BallotCreate) -> dict:
    options_json = json.dumps(ballot.options)
    if ballot.voting_period_start:
        bid = execute(
            """INSERT INTO ballots (title, description, ballot_type, options,
               voting_period_start, voting_period_end, created_by)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (ballot.title, ballot.description, ballot.ballot_type, options_json,
             ballot.voting_period_start, ballot.voting_period_end, ballot.created_by),
        )
    else:
        bid = execute(
            """INSERT INTO ballots (title, description, ballot_type, options,
               voting_period_end, created_by)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (ballot.title, ballot.description, ballot.ballot_type, options_json,
             ballot.voting_period_end, ballot.created_by),
        )
    return get_ballot(bid)


@router.post("/ballots/{ballot_id}/vote", status_code=201)
def cast_vote(ballot_id: int, vote: VoteCast) -> dict:
    ballot = query("SELECT * FROM ballots WHERE id = ?", (ballot_id,))
    if not ballot:
        raise HTTPException(status_code=404, detail="Ballot not found")
    # Check one person one vote
    existing = query(
        "SELECT id FROM votes WHERE ballot_id = ? AND voter_id = ?",
        (ballot_id, vote.voter_id),
    )
    if existing:
        raise HTTPException(status_code=409, detail="Already voted on this ballot")
    options = json.loads(ballot[0]["options"])
    # For ranked choice, choice is a comma-separated ranking
    if ballot[0]["ballot_type"] == "ranked_choice":
        ranked = [c.strip() for c in vote.choice.split(",")]
        for c in ranked:
            if c not in options:
                raise HTTPException(status_code=400, detail=f"Invalid option: {c}")
    else:
        if vote.choice not in options:
            raise HTTPException(status_code=400, detail=f"Invalid choice. Options: {options}")
    vid = execute(
        "INSERT INTO votes (ballot_id, voter_id, choice) VALUES (?, ?, ?)",
        (ballot_id, vote.voter_id, vote.choice),
    )
    # Audit log
    execute(
        "INSERT INTO vote_audit_log (ballot_id, voter_id, action, detail) VALUES (?, ?, ?, ?)",
        (ballot_id, vote.voter_id, "vote_cast", vote.choice),
    )
    return {"id": vid, "ballot_id": ballot_id, "voter_id": vote.voter_id, "choice": vote.choice}


@router.get("/ballots/{ballot_id}/results")
def get_results(ballot_id: int) -> dict:
    ballot = query("SELECT * FROM ballots WHERE id = ?", (ballot_id,))
    if not ballot:
        raise HTTPException(status_code=404, detail="Ballot not found")
    ballot_data = ballot[0]
    options = json.loads(ballot_data["options"])
    votes = query(
        "SELECT choice, COUNT(*) as count FROM votes WHERE ballot_id = ? GROUP BY choice",
        (ballot_id,),
    )
    total = sum(v["count"] for v in votes)
    tally = {opt: 0 for opt in options}
    for v in votes:
        tally[v["choice"]] = v["count"]
    return {
        "ballot_id": ballot_id,
        "title": ballot_data["title"],
        "ballot_type": ballot_data["ballot_type"],
        "total_votes": total,
        "tally": tally,
    }


@router.get("/ballots/{ballot_id}/audit")
def get_audit_log(ballot_id: int) -> list[dict]:
    return query(
        "SELECT * FROM vote_audit_log WHERE ballot_id = ? ORDER BY logged_at",
        (ballot_id,),
    )
