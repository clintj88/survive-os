"""Workflow, state, and transition CRUD endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .auth import require_medical_role
from .database import execute, query

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


class WorkflowCreate(BaseModel):
    program_id: int
    name: str
    description: str = ""


class StateCreate(BaseModel):
    name: str
    initial: bool = False
    terminal: bool = False
    sort_order: int = 0


class TransitionCreate(BaseModel):
    from_state_id: int
    to_state_id: int


@router.get("")
def list_workflows(
    program_id: Optional[int] = None,
    user: str = Depends(require_medical_role),
) -> list[dict]:
    if program_id is not None:
        return query(
            "SELECT * FROM program_workflows WHERE program_id = ? ORDER BY name",
            (program_id,),
        )
    return query("SELECT * FROM program_workflows ORDER BY name")


@router.get("/{workflow_id}")
def get_workflow(workflow_id: int, user: str = Depends(require_medical_role)) -> dict:
    results = query("SELECT * FROM program_workflows WHERE id = ?", (workflow_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Workflow not found")
    workflow = results[0]
    workflow["states"] = query(
        "SELECT * FROM workflow_states WHERE workflow_id = ? ORDER BY sort_order",
        (workflow_id,),
    )
    for state in workflow["states"]:
        state["transitions"] = query(
            """SELECT st.id, st.to_state_id, ws.name as to_state_name
               FROM state_transitions st
               JOIN workflow_states ws ON st.to_state_id = ws.id
               WHERE st.from_state_id = ?""",
            (state["id"],),
        )
    return workflow


@router.post("", status_code=201)
def create_workflow(workflow: WorkflowCreate, user: str = Depends(require_medical_role)) -> dict:
    prog = query("SELECT id FROM programs WHERE id = ?", (workflow.program_id,))
    if not prog:
        raise HTTPException(status_code=404, detail="Program not found")
    row_id = execute(
        "INSERT INTO program_workflows (program_id, name, description) VALUES (?, ?, ?)",
        (workflow.program_id, workflow.name, workflow.description),
    )
    return get_workflow(row_id, user)


@router.delete("/{workflow_id}", status_code=204)
def delete_workflow(workflow_id: int, user: str = Depends(require_medical_role)) -> None:
    existing = query("SELECT id FROM program_workflows WHERE id = ?", (workflow_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Workflow not found")
    execute("DELETE FROM program_workflows WHERE id = ?", (workflow_id,))


# --- States ---

@router.post("/{workflow_id}/states", status_code=201)
def create_state(
    workflow_id: int,
    state: StateCreate,
    user: str = Depends(require_medical_role),
) -> dict:
    existing = query("SELECT id FROM program_workflows WHERE id = ?", (workflow_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Workflow not found")
    row_id = execute(
        """INSERT INTO workflow_states (workflow_id, name, initial, terminal, sort_order)
           VALUES (?, ?, ?, ?, ?)""",
        (workflow_id, state.name, 1 if state.initial else 0, 1 if state.terminal else 0, state.sort_order),
    )
    results = query("SELECT * FROM workflow_states WHERE id = ?", (row_id,))
    return results[0]


@router.get("/{workflow_id}/states")
def list_states(workflow_id: int, user: str = Depends(require_medical_role)) -> list[dict]:
    existing = query("SELECT id FROM program_workflows WHERE id = ?", (workflow_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return query(
        "SELECT * FROM workflow_states WHERE workflow_id = ? ORDER BY sort_order",
        (workflow_id,),
    )


@router.delete("/states/{state_id}", status_code=204)
def delete_state(state_id: int, user: str = Depends(require_medical_role)) -> None:
    existing = query("SELECT id FROM workflow_states WHERE id = ?", (state_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="State not found")
    execute("DELETE FROM workflow_states WHERE id = ?", (state_id,))


# --- Transitions ---

@router.post("/transitions", status_code=201)
def create_transition(
    transition: TransitionCreate,
    user: str = Depends(require_medical_role),
) -> dict:
    from_state = query("SELECT * FROM workflow_states WHERE id = ?", (transition.from_state_id,))
    if not from_state:
        raise HTTPException(status_code=404, detail="From state not found")
    to_state = query("SELECT * FROM workflow_states WHERE id = ?", (transition.to_state_id,))
    if not to_state:
        raise HTTPException(status_code=404, detail="To state not found")
    if from_state[0]["workflow_id"] != to_state[0]["workflow_id"]:
        raise HTTPException(status_code=400, detail="States must belong to the same workflow")

    row_id = execute(
        "INSERT INTO state_transitions (from_state_id, to_state_id) VALUES (?, ?)",
        (transition.from_state_id, transition.to_state_id),
    )
    results = query(
        """SELECT st.*, ws.name as to_state_name
           FROM state_transitions st
           JOIN workflow_states ws ON st.to_state_id = ws.id
           WHERE st.id = ?""",
        (row_id,),
    )
    return results[0]


@router.delete("/transitions/{transition_id}", status_code=204)
def delete_transition(transition_id: int, user: str = Depends(require_medical_role)) -> None:
    existing = query("SELECT id FROM state_transitions WHERE id = ?", (transition_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Transition not found")
    execute("DELETE FROM state_transitions WHERE id = ?", (transition_id,))
