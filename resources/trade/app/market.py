"""Market day management for coordinating community trading events."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database import execute, query

logger = logging.getLogger("survive-trade")

router = APIRouter(prefix="/api/market", tags=["market"])

_redis_client = None


def set_redis(client: object) -> None:
    global _redis_client
    _redis_client = client


class MarketDayCreate(BaseModel):
    date: str
    location: str
    organizer: str


class MarketDayUpdate(BaseModel):
    status: Optional[str] = None
    location: Optional[str] = None


class ListingCreate(BaseModel):
    person: str
    item_description: str
    quantity: float
    unit: str
    asking_price_hours: float = 0
    type: str = "offer"  # 'offer' or 'want'


@router.get("")
def list_market_days(status: Optional[str] = None) -> list[dict]:
    if status:
        return query(
            """SELECT id, date, location, organizer, status, created_at, updated_at
               FROM market_days WHERE status = ? ORDER BY date DESC""",
            (status,),
        )
    return query(
        """SELECT id, date, location, organizer, status, created_at, updated_at
           FROM market_days ORDER BY date DESC"""
    )


@router.get("/{market_id}")
def get_market_day(market_id: int) -> dict:
    results = query(
        """SELECT id, date, location, organizer, status, created_at, updated_at
           FROM market_days WHERE id = ?""",
        (market_id,),
    )
    if not results:
        raise HTTPException(status_code=404, detail="Market day not found")
    market = results[0]
    market["listings"] = query(
        """SELECT id, person, item_description, quantity, unit,
                  asking_price_hours, type, created_at
           FROM market_listings WHERE market_id = ? ORDER BY type, person""",
        (market_id,),
    )
    return market


@router.post("", status_code=201)
def create_market_day(market: MarketDayCreate) -> dict:
    market_id = execute(
        """INSERT INTO market_days (date, location, organizer)
           VALUES (?, ?, ?)""",
        (market.date, market.location, market.organizer),
    )

    # Publish announcement via Redis
    if _redis_client:
        try:
            _redis_client.publish(
                "resources.market-day",
                json.dumps({
                    "event": "market_day_created",
                    "market_id": market_id,
                    "date": market.date,
                    "location": market.location,
                    "organizer": market.organizer,
                }),
            )
        except Exception as e:
            logger.warning("Failed to publish market day announcement: %s", e)

    return get_market_day(market_id)


@router.patch("/{market_id}")
def update_market_day(market_id: int, update: MarketDayUpdate) -> dict:
    existing = query("SELECT id FROM market_days WHERE id = ?", (market_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Market day not found")

    updates: list[str] = []
    params: list = []
    if update.status is not None:
        if update.status not in ("upcoming", "active", "completed"):
            raise HTTPException(status_code=400, detail=f"Invalid status: {update.status}")
        updates.append("status = ?")
        params.append(update.status)
    if update.location is not None:
        updates.append("location = ?")
        params.append(update.location)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.append(market_id)
    execute(f"UPDATE market_days SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_market_day(market_id)


@router.post("/{market_id}/listings", status_code=201)
def add_listing(market_id: int, listing: ListingCreate) -> dict:
    existing = query("SELECT id FROM market_days WHERE id = ?", (market_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Market day not found")
    if listing.type not in ("offer", "want"):
        raise HTTPException(status_code=400, detail=f"Invalid listing type: {listing.type}")

    listing_id = execute(
        """INSERT INTO market_listings
               (market_id, person, item_description, quantity, unit, asking_price_hours, type)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (market_id, listing.person, listing.item_description,
         listing.quantity, listing.unit, listing.asking_price_hours, listing.type),
    )
    results = query("SELECT * FROM market_listings WHERE id = ?", (listing_id,))
    return results[0]


@router.get("/{market_id}/listings")
def list_listings(market_id: int, type: Optional[str] = None) -> list[dict]:
    existing = query("SELECT id FROM market_days WHERE id = ?", (market_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Market day not found")
    if type:
        return query(
            """SELECT id, person, item_description, quantity, unit,
                      asking_price_hours, type, created_at
               FROM market_listings WHERE market_id = ? AND type = ?
               ORDER BY person""",
            (market_id, type),
        )
    return query(
        """SELECT id, person, item_description, quantity, unit,
                  asking_price_hours, type, created_at
           FROM market_listings WHERE market_id = ?
           ORDER BY type, person""",
        (market_id,),
    )
