"""Location management for inventory storage."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .audit import log_action
from .database import VALID_LOCATION_TYPES, execute, query

router = APIRouter(prefix="/api/locations", tags=["locations"])


class LocationCreate(BaseModel):
    name: str
    type: str = "warehouse"
    description: str = ""
    capacity: Optional[int] = None


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    capacity: Optional[int] = None


class TransferRequest(BaseModel):
    item_id: int
    to_location_id: int
    quantity: Optional[float] = None
    transferred_by: str = ""
    notes: str = ""


def _get_location(location_id: int) -> dict:
    results = query("SELECT * FROM locations WHERE id = ?", (location_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Location not found")
    return results[0]


@router.get("")
def list_locations() -> list[dict]:
    locations = query("SELECT * FROM locations ORDER BY name")
    for loc in locations:
        item_count = query(
            "SELECT COUNT(*) as count, COALESCE(SUM(quantity), 0) as total_quantity FROM items WHERE location_id = ?",
            (loc["id"],),
        )
        loc["item_count"] = item_count[0]["count"]
        loc["total_quantity"] = item_count[0]["total_quantity"]
    return locations


@router.get("/{location_id}")
def get_location(location_id: int) -> dict:
    return _get_location(location_id)


@router.post("", status_code=201)
def create_location(location: LocationCreate) -> dict:
    if location.type not in VALID_LOCATION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid type. Must be one of: {', '.join(VALID_LOCATION_TYPES)}",
        )

    existing = query("SELECT id FROM locations WHERE name = ?", (location.name,))
    if existing:
        raise HTTPException(status_code=400, detail="Location name already exists")

    loc_id = execute(
        "INSERT INTO locations (name, type, description, capacity) VALUES (?, ?, ?, ?)",
        (location.name, location.type, location.description, location.capacity),
    )
    return _get_location(loc_id)


@router.put("/{location_id}")
def update_location(location_id: int, location: LocationUpdate) -> dict:
    _get_location(location_id)

    fields = location.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    if "type" in fields and fields["type"] not in VALID_LOCATION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid type. Must be one of: {', '.join(VALID_LOCATION_TYPES)}",
        )

    updates = [f"{k} = ?" for k in fields]
    params = list(fields.values()) + [location_id]

    execute(f"UPDATE locations SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return _get_location(location_id)


@router.delete("/{location_id}")
def delete_location(location_id: int) -> dict:
    _get_location(location_id)

    items_at_loc = query("SELECT COUNT(*) as count FROM items WHERE location_id = ?", (location_id,))
    if items_at_loc[0]["count"] > 0:
        raise HTTPException(status_code=400, detail="Cannot delete location with items assigned")

    execute("DELETE FROM locations WHERE id = ?", (location_id,))
    return {"detail": "Location deleted"}


@router.get("/{location_id}/items")
def location_items(location_id: int) -> list[dict]:
    _get_location(location_id)
    return query(
        "SELECT * FROM items WHERE location_id = ? ORDER BY name",
        (location_id,),
    )


@router.post("/transfer")
def transfer_item(transfer: TransferRequest) -> dict:
    items = query("SELECT id, name, quantity, location_id FROM items WHERE id = ?", (transfer.item_id,))
    if not items:
        raise HTTPException(status_code=404, detail="Item not found")

    item = items[0]
    to_loc = _get_location(transfer.to_location_id)

    from_location_id = item["location_id"]
    from_name = "unassigned"
    if from_location_id:
        from_loc = query("SELECT name FROM locations WHERE id = ?", (from_location_id,))
        if from_loc:
            from_name = from_loc[0]["name"]

    execute(
        "UPDATE items SET location_id = ?, updated_at = datetime('now') WHERE id = ?",
        (transfer.to_location_id, transfer.item_id),
    )

    log_action(
        transfer.item_id, "transfer", transfer.transferred_by,
        notes=f"Transferred from '{from_name}' to '{to_loc['name']}'. {transfer.notes}".strip(),
    )

    return {
        "item_id": transfer.item_id,
        "item_name": item["name"],
        "from_location": from_name,
        "to_location": to_loc["name"],
    }
