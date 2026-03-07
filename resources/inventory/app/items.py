"""Item CRUD operations for inventory management."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .audit import log_action
from .database import VALID_CATEGORIES, VALID_CONDITIONS, execute, query

router = APIRouter(prefix="/api/items", tags=["items"])


class ItemCreate(BaseModel):
    name: str
    category: str
    subcategory: str = ""
    quantity: float = 0
    unit: str = "count"
    expiration_date: Optional[str] = None
    condition: str = "good"
    notes: str = ""
    location_id: Optional[int] = None


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    expiration_date: Optional[str] = None
    condition: Optional[str] = None
    notes: Optional[str] = None
    location_id: Optional[int] = None


class BatchImport(BaseModel):
    items: list[ItemCreate]
    performed_by: str = ""


def _get_item(item_id: int) -> dict:
    results = query(
        """SELECT i.*, l.name as location_name
           FROM items i LEFT JOIN locations l ON i.location_id = l.id
           WHERE i.id = ?""",
        (item_id,),
    )
    if not results:
        raise HTTPException(status_code=404, detail="Item not found")
    return results[0]


@router.get("")
def list_items(
    category: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    location_id: Optional[int] = Query(None),
    condition: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> list[dict]:
    conditions: list[str] = []
    params: list = []

    if category:
        conditions.append("i.category = ?")
        params.append(category)
    if name:
        conditions.append("i.name LIKE ?")
        params.append(f"%{name}%")
    if location_id is not None:
        conditions.append("i.location_id = ?")
        params.append(location_id)
    if condition:
        conditions.append("i.condition = ?")
        params.append(condition)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.extend([limit, offset])

    return query(
        f"""SELECT i.*, l.name as location_name
            FROM items i LEFT JOIN locations l ON i.location_id = l.id
            {where}
            ORDER BY i.name
            LIMIT ? OFFSET ?""",
        tuple(params),
    )


@router.get("/{item_id}")
def get_item(item_id: int) -> dict:
    return _get_item(item_id)


@router.post("", status_code=201)
def create_item(item: ItemCreate, performed_by: str = Query("")) -> dict:
    if item.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}")
    if item.condition not in VALID_CONDITIONS:
        raise HTTPException(status_code=400, detail=f"Invalid condition. Must be one of: {', '.join(VALID_CONDITIONS)}")

    if item.location_id is not None:
        loc = query("SELECT id FROM locations WHERE id = ?", (item.location_id,))
        if not loc:
            raise HTTPException(status_code=400, detail="Location not found")

    qr_code = f"INV-{uuid.uuid4().hex[:8].upper()}"

    item_id = execute(
        """INSERT INTO items (name, category, subcategory, quantity, unit,
           expiration_date, condition, notes, location_id, qr_code)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            item.name, item.category, item.subcategory, item.quantity,
            item.unit, item.expiration_date, item.condition, item.notes,
            item.location_id, qr_code,
        ),
    )

    log_action(item_id, "create", performed_by, item.quantity, 0, item.quantity,
               f"Created item: {item.name}")

    return _get_item(item_id)


@router.put("/{item_id}")
def update_item(item_id: int, item: ItemUpdate, performed_by: str = Query("")) -> dict:
    existing = _get_item(item_id)

    if item.category is not None and item.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}")
    if item.condition is not None and item.condition not in VALID_CONDITIONS:
        raise HTTPException(status_code=400, detail=f"Invalid condition. Must be one of: {', '.join(VALID_CONDITIONS)}")

    updates: list[str] = []
    params: list = []
    fields = item.model_dump(exclude_unset=True)

    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    for field, value in fields.items():
        updates.append(f"{field} = ?")
        params.append(value)

    updates.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.append(item_id)

    execute(f"UPDATE items SET {', '.join(updates)} WHERE id = ?", tuple(params))

    quantity_change = None
    if item.quantity is not None:
        quantity_change = item.quantity - existing["quantity"]

    log_action(
        item_id, "update", performed_by,
        quantity_change, existing["quantity"],
        item.quantity if item.quantity is not None else existing["quantity"],
        f"Updated item fields: {', '.join(fields.keys())}",
    )

    return _get_item(item_id)


@router.delete("/{item_id}")
def delete_item(item_id: int, performed_by: str = Query("")) -> dict:
    existing = _get_item(item_id)
    execute("DELETE FROM items WHERE id = ?", (item_id,))
    log_action(item_id, "delete", performed_by, notes=f"Deleted item: {existing['name']}")
    return {"detail": "Item deleted"}


@router.post("/batch", status_code=201)
def batch_import(batch: BatchImport) -> dict:
    created = []
    errors = []
    for i, item in enumerate(batch.items):
        try:
            result = create_item(item, performed_by=batch.performed_by)
            created.append(result)
        except HTTPException as e:
            errors.append({"index": i, "name": item.name, "error": e.detail})
    return {"created": len(created), "errors": errors, "items": created}
