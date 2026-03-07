"""Seed exchange system for cross-community trading."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/exchange", tags=["exchange"])


class ExchangeListingCreate(BaseModel):
    lot_id: Optional[int] = None
    type: str  # offer or request
    species: str
    variety: str = ""
    quantity_available: float = 0
    unit: str = "grams"
    description: str = ""
    contact: str = ""
    community: str = "local"


class ExchangeListingUpdate(BaseModel):
    quantity_available: Optional[float] = None
    description: Optional[str] = None
    status: Optional[str] = None


@router.get("/listings")
def list_listings(
    type: Optional[str] = Query(None),
    species: Optional[str] = Query(None),
    status: str = Query("active"),
) -> list[dict]:
    conditions = ["status = ?"]
    params: list = [status]
    if type:
        conditions.append("type = ?")
        params.append(type)
    if species:
        conditions.append("species = ?")
        params.append(species)
    where = f"WHERE {' AND '.join(conditions)}"
    return query(
        f"SELECT * FROM exchange_listings {where} ORDER BY created_at DESC",
        tuple(params),
    )


@router.post("/listings", status_code=201)
def create_listing(listing: ExchangeListingCreate) -> dict:
    if listing.type not in ("offer", "request"):
        raise HTTPException(status_code=400, detail="Type must be 'offer' or 'request'")
    if listing.lot_id:
        lot = query("SELECT id FROM seed_lots WHERE id = ?", (listing.lot_id,))
        if not lot:
            raise HTTPException(status_code=404, detail="Seed lot not found")

    listing_id = execute(
        """INSERT INTO exchange_listings
           (lot_id, type, species, variety, quantity_available, unit, description, contact, community)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            listing.lot_id, listing.type, listing.species, listing.variety,
            listing.quantity_available, listing.unit, listing.description,
            listing.contact, listing.community,
        ),
    )
    results = query("SELECT * FROM exchange_listings WHERE id = ?", (listing_id,))
    return results[0]


@router.put("/listings/{listing_id}")
def update_listing(listing_id: int, listing: ExchangeListingUpdate) -> dict:
    existing = query("SELECT id FROM exchange_listings WHERE id = ?", (listing_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Listing not found")

    updates: list[str] = []
    params: list = []
    if listing.quantity_available is not None:
        updates.append("quantity_available = ?")
        params.append(listing.quantity_available)
    if listing.description is not None:
        updates.append("description = ?")
        params.append(listing.description)
    if listing.status is not None:
        if listing.status not in ("active", "fulfilled", "cancelled"):
            raise HTTPException(status_code=400, detail="Invalid status")
        updates.append("status = ?")
        params.append(listing.status)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.append(listing_id)
    execute(f"UPDATE exchange_listings SET {', '.join(updates)} WHERE id = ?", tuple(params))

    results = query("SELECT * FROM exchange_listings WHERE id = ?", (listing_id,))
    return results[0]


@router.delete("/listings/{listing_id}", status_code=204)
def delete_listing(listing_id: int) -> None:
    existing = query("SELECT id FROM exchange_listings WHERE id = ?", (listing_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Listing not found")
    execute("DELETE FROM exchange_listings WHERE id = ?", (listing_id,))
