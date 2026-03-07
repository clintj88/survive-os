"""Civil Registry routes - births, deaths, marriages."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/registry", tags=["registry"])


class BirthRecord(BaseModel):
    child_name: str
    dob: str
    parent1: str = ""
    parent2: str = ""
    location: str = ""
    attendant: str = ""


class DeathRecord(BaseModel):
    person_name: str
    date_of_death: str
    cause: str = ""
    location: str = ""
    witnessed_by: str = ""


class MarriageRecord(BaseModel):
    party1: str
    party2: str
    marriage_date: str
    officiant: str = ""
    witnesses: str = ""


@router.get("/births")
def list_births() -> list[dict]:
    return query("SELECT * FROM birth_records ORDER BY dob DESC")


@router.post("/births", status_code=201)
def create_birth(record: BirthRecord) -> dict:
    bid = execute(
        "INSERT INTO birth_records (child_name, dob, parent1, parent2, location, attendant) VALUES (?, ?, ?, ?, ?, ?)",
        (record.child_name, record.dob, record.parent1, record.parent2, record.location, record.attendant),
    )
    results = query("SELECT * FROM birth_records WHERE id = ?", (bid,))
    return results[0]


@router.get("/deaths")
def list_deaths() -> list[dict]:
    return query("SELECT * FROM death_records ORDER BY date_of_death DESC")


@router.post("/deaths", status_code=201)
def create_death(record: DeathRecord) -> dict:
    did = execute(
        "INSERT INTO death_records (person_name, date_of_death, cause, location, witnessed_by) VALUES (?, ?, ?, ?, ?)",
        (record.person_name, record.date_of_death, record.cause, record.location, record.witnessed_by),
    )
    results = query("SELECT * FROM death_records WHERE id = ?", (did,))
    return results[0]


@router.get("/marriages")
def list_marriages() -> list[dict]:
    return query("SELECT * FROM marriage_records ORDER BY marriage_date DESC")


@router.post("/marriages", status_code=201)
def create_marriage(record: MarriageRecord) -> dict:
    mid = execute(
        "INSERT INTO marriage_records (party1, party2, marriage_date, officiant, witnesses) VALUES (?, ?, ?, ?, ?)",
        (record.party1, record.party2, record.marriage_date, record.officiant, record.witnesses),
    )
    results = query("SELECT * FROM marriage_records WHERE id = ?", (mid,))
    return results[0]
