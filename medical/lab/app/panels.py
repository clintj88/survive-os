"""Lab panels router — CRUD for test panels (groups of tests)."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .auth import require_medical_role
from .database import execute, query

router = APIRouter(prefix="/api/panels", tags=["panels"])


class PanelCreate(BaseModel):
    name: str
    description: str = ""
    test_ids: list[int] = []


class PanelUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    test_ids: list[int] | None = None


def _enrich_panel(panel: dict) -> dict:
    """Add tests list to a panel dict."""
    tests = query(
        """SELECT tc.* FROM panel_tests pt
           JOIN test_catalog tc ON tc.id = pt.test_id
           WHERE pt.panel_id = ?
           ORDER BY pt.sort_order""",
        (panel["id"],),
    )
    panel["tests"] = tests
    return panel


@router.get("")
def list_panels(_user: str = Depends(require_medical_role)) -> list[dict]:
    panels = query("SELECT * FROM lab_panels ORDER BY name")
    return [_enrich_panel(p) for p in panels]


@router.get("/{panel_id}")
def get_panel(panel_id: int, _user: str = Depends(require_medical_role)) -> dict:
    rows = query("SELECT * FROM lab_panels WHERE id = ?", (panel_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Panel not found")
    return _enrich_panel(rows[0])


@router.post("", status_code=201)
def create_panel(body: PanelCreate, _user: str = Depends(require_medical_role)) -> dict:
    panel_id = execute(
        "INSERT INTO lab_panels (name, description) VALUES (?, ?)",
        (body.name, body.description),
    )
    for i, test_id in enumerate(body.test_ids):
        execute(
            "INSERT INTO panel_tests (panel_id, test_id, sort_order) VALUES (?, ?, ?)",
            (panel_id, test_id, i),
        )
    return get_panel(panel_id, _user)


@router.put("/{panel_id}")
def update_panel(
    panel_id: int, body: PanelUpdate, _user: str = Depends(require_medical_role),
) -> dict:
    existing = query("SELECT * FROM lab_panels WHERE id = ?", (panel_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Panel not found")
    updates = body.model_dump(exclude_unset=True)
    test_ids = updates.pop("test_ids", None)
    if updates:
        sets = ", ".join(f"{k} = ?" for k in updates)
        vals = list(updates.values())
        vals.append(panel_id)
        execute(f"UPDATE lab_panels SET {sets} WHERE id = ?", tuple(vals))
    if test_ids is not None:
        execute("DELETE FROM panel_tests WHERE panel_id = ?", (panel_id,))
        for i, tid in enumerate(test_ids):
            execute(
                "INSERT INTO panel_tests (panel_id, test_id, sort_order) VALUES (?, ?, ?)",
                (panel_id, tid, i),
            )
    return get_panel(panel_id, _user)


@router.delete("/{panel_id}", status_code=204)
def delete_panel(panel_id: int, _user: str = Depends(require_medical_role)) -> None:
    existing = query("SELECT * FROM lab_panels WHERE id = ?", (panel_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Panel not found")
    execute("DELETE FROM panel_tests WHERE panel_id = ?", (panel_id,))
    execute("DELETE FROM lab_panels WHERE id = ?", (panel_id,))
