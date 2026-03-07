"""Seed data for clinical programs with workflows and state transitions."""

from app.database import execute, query


def seed() -> None:
    """Load pre-defined clinical programs if none exist."""
    existing = query("SELECT COUNT(*) as count FROM programs")
    if existing[0]["count"] > 0:
        return

    _seed_tb()
    _seed_hiv()
    _seed_diabetes()
    _seed_prenatal()


def _create_program(name: str, description: str) -> int:
    return execute(
        "INSERT INTO programs (name, description) VALUES (?, ?)",
        (name, description),
    )


def _create_workflow(program_id: int, name: str, description: str) -> int:
    return execute(
        "INSERT INTO program_workflows (program_id, name, description) VALUES (?, ?, ?)",
        (program_id, name, description),
    )


def _create_state(workflow_id: int, name: str, initial: bool, terminal: bool, sort_order: int) -> int:
    return execute(
        "INSERT INTO workflow_states (workflow_id, name, initial, terminal, sort_order) VALUES (?, ?, ?, ?, ?)",
        (workflow_id, name, 1 if initial else 0, 1 if terminal else 0, sort_order),
    )


def _create_transition(from_id: int, to_id: int) -> None:
    execute(
        "INSERT INTO state_transitions (from_state_id, to_state_id) VALUES (?, ?)",
        (from_id, to_id),
    )


def _seed_tb() -> None:
    prog = _create_program("TB Treatment", "Tuberculosis treatment program following WHO DOTS strategy")
    wf = _create_workflow(prog, "TB Treatment Workflow", "Standard TB treatment pathway")

    screening = _create_state(wf, "screening", True, False, 1)
    diagnosed = _create_state(wf, "diagnosed", False, False, 2)
    intensive = _create_state(wf, "intensive_phase", False, False, 3)
    continuation = _create_state(wf, "continuation_phase", False, False, 4)
    completed = _create_state(wf, "completed", False, True, 5)
    defaulted = _create_state(wf, "defaulted", False, True, 6)
    transferred = _create_state(wf, "transferred", False, True, 7)

    _create_transition(screening, diagnosed)
    _create_transition(diagnosed, intensive)
    _create_transition(intensive, continuation)
    _create_transition(continuation, completed)
    _create_transition(intensive, defaulted)
    _create_transition(continuation, defaulted)
    _create_transition(intensive, transferred)
    _create_transition(continuation, transferred)


def _seed_hiv() -> None:
    prog = _create_program("HIV Care", "HIV care and treatment program")
    wf = _create_workflow(prog, "HIV Care Workflow", "Standard HIV care pathway")

    testing = _create_state(wf, "testing", True, False, 1)
    enrolled = _create_state(wf, "enrolled", False, False, 2)
    on_art = _create_state(wf, "on_art", False, False, 3)
    viral_suppression = _create_state(wf, "viral_suppression", False, True, 4)
    lost = _create_state(wf, "lost_to_followup", False, True, 5)

    _create_transition(testing, enrolled)
    _create_transition(enrolled, on_art)
    _create_transition(on_art, viral_suppression)
    _create_transition(on_art, lost)
    _create_transition(enrolled, lost)


def _seed_diabetes() -> None:
    prog = _create_program("Diabetes Management", "Type 2 diabetes management program")
    wf = _create_workflow(prog, "Diabetes Workflow", "Diabetes management pathway")

    screening = _create_state(wf, "screening", True, False, 1)
    active = _create_state(wf, "active_management", False, False, 2)
    controlled = _create_state(wf, "controlled", False, True, 3)
    uncontrolled = _create_state(wf, "uncontrolled", False, True, 4)

    _create_transition(screening, active)
    _create_transition(active, controlled)
    _create_transition(active, uncontrolled)


def _seed_prenatal() -> None:
    prog = _create_program("Prenatal Care", "Prenatal care and delivery program")
    wf = _create_workflow(prog, "Prenatal Workflow", "Standard prenatal care pathway")

    initial = _create_state(wf, "initial_visit", True, False, 1)
    first = _create_state(wf, "first_trimester", False, False, 2)
    second = _create_state(wf, "second_trimester", False, False, 3)
    third = _create_state(wf, "third_trimester", False, False, 4)
    delivered = _create_state(wf, "delivered", False, True, 5)
    complicated = _create_state(wf, "complicated", False, True, 6)

    _create_transition(initial, first)
    _create_transition(first, second)
    _create_transition(second, third)
    _create_transition(third, delivered)
    _create_transition(first, complicated)
    _create_transition(second, complicated)
    _create_transition(third, complicated)
