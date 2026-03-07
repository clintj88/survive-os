"""Resource Allocation routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/resources", tags=["resources"])


class ResourceCreate(BaseModel):
    category: str
    name: str
    quantity: float = 0
    unit: str = "units"
    low_threshold: float = 10


class ResourceUpdate(BaseModel):
    quantity: Optional[float] = None
    low_threshold: Optional[float] = None


class DistributionRecord(BaseModel):
    resource_id: int
    person_id: int
    quantity: float
    distributed_by: str = ""


class RationRequest(BaseModel):
    resource_id: int
    days: int = 7


@router.get("/inventory")
def list_inventory(category: Optional[str] = Query(None)) -> list[dict]:
    if category:
        return query(
            "SELECT * FROM resource_inventory WHERE category = ? ORDER BY name",
            (category,),
        )
    return query("SELECT * FROM resource_inventory ORDER BY category, name")


@router.get("/inventory/{resource_id}")
def get_resource(resource_id: int) -> dict:
    results = query("SELECT * FROM resource_inventory WHERE id = ?", (resource_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Resource not found")
    return results[0]


@router.post("/inventory", status_code=201)
def create_resource(resource: ResourceCreate) -> dict:
    rid = execute(
        """INSERT INTO resource_inventory (category, name, quantity, unit, low_threshold)
           VALUES (?, ?, ?, ?, ?)""",
        (resource.category, resource.name, resource.quantity, resource.unit, resource.low_threshold),
    )
    return get_resource(rid)


@router.put("/inventory/{resource_id}")
def update_resource(resource_id: int, resource: ResourceUpdate) -> dict:
    existing = query("SELECT id FROM resource_inventory WHERE id = ?", (resource_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Resource not found")
    updates: list[str] = []
    params: list = []
    if resource.quantity is not None:
        updates.append("quantity = ?")
        params.append(resource.quantity)
    if resource.low_threshold is not None:
        updates.append("low_threshold = ?")
        params.append(resource.low_threshold)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    updates.append("updated_at = datetime('now')")
    params.append(resource_id)
    execute(f"UPDATE resource_inventory SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_resource(resource_id)


@router.post("/distribute", status_code=201)
def distribute_resource(dist: DistributionRecord) -> dict:
    resource = query("SELECT * FROM resource_inventory WHERE id = ?", (dist.resource_id,))
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    if resource[0]["quantity"] < dist.quantity:
        raise HTTPException(status_code=400, detail="Insufficient quantity")
    execute(
        "UPDATE resource_inventory SET quantity = quantity - ?, updated_at = datetime('now') WHERE id = ?",
        (dist.quantity, dist.resource_id),
    )
    did = execute(
        """INSERT INTO distribution_log (resource_id, person_id, quantity, distributed_by)
           VALUES (?, ?, ?, ?)""",
        (dist.resource_id, dist.person_id, dist.quantity, dist.distributed_by),
    )
    return {"id": did, **dist.model_dump()}


@router.get("/distribution-log")
def get_distribution_log(
    resource_id: Optional[int] = Query(None),
    person_id: Optional[int] = Query(None),
) -> list[dict]:
    sql = "SELECT * FROM distribution_log WHERE 1=1"
    params: list = []
    if resource_id:
        sql += " AND resource_id = ?"
        params.append(resource_id)
    if person_id:
        sql += " AND person_id = ?"
        params.append(person_id)
    sql += " ORDER BY distributed_at DESC"
    return query(sql, tuple(params))


@router.post("/ration-calculator")
def calculate_rations(req: RationRequest) -> dict:
    resource = query("SELECT * FROM resource_inventory WHERE id = ?", (req.resource_id,))
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    population = query("SELECT COUNT(*) as count FROM persons WHERE status = 'active'")
    pop_count = population[0]["count"] if population else 0
    if pop_count == 0:
        raise HTTPException(status_code=400, detail="No active population")
    r = resource[0]
    per_person_total = r["quantity"] / pop_count
    per_person_per_day = per_person_total / req.days if req.days > 0 else 0
    return {
        "resource": r["name"],
        "category": r["category"],
        "total_quantity": r["quantity"],
        "unit": r["unit"],
        "population": pop_count,
        "days": req.days,
        "per_person_total": round(per_person_total, 2),
        "per_person_per_day": round(per_person_per_day, 2),
    }


@router.get("/alerts")
def low_resource_alerts() -> list[dict]:
    return query(
        "SELECT * FROM resource_inventory WHERE quantity <= low_threshold ORDER BY quantity ASC"
    )
