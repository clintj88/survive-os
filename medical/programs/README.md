# Program Enrollment - SURVIVE OS Medical

Patient enrollment and tracking through structured clinical programs with multi-state workflows, transition validation, and outcome recording.

## Features

- Program management with active/inactive status
- Multi-state workflows with defined transitions
- Patient enrollment with automatic initial state placement
- State transition validation (only allowed transitions permitted)
- Auto-completion on terminal state transitions
- Full enrollment state history with timestamps and reasons
- Outcome tracking: completed, defaulted, transferred_out, died
- Dashboard with active enrollments per program grouped by state
- Pre-seeded programs: TB Treatment, HIV Care, Diabetes Management, Prenatal Care
- Optional SQLCipher encryption at rest
- Role-based access: requires `X-Role: medical` header

## API

### Programs
- `GET /health` - Health check
- `GET /api/programs` - List programs
- `GET /api/programs/{id}` - Get program
- `POST /api/programs` - Create program
- `PUT /api/programs/{id}` - Update program
- `DELETE /api/programs/{id}` - Delete program (cascades)
- `GET /api/programs/dashboard` - Active enrollments by program and state
- `GET /api/programs/{id}/enrollments` - List enrollments (filter: `status`)

### Workflows
- `GET /api/workflows` - List workflows (filter: `program_id`)
- `GET /api/workflows/{id}` - Get workflow with states and transitions
- `POST /api/workflows` - Create workflow
- `DELETE /api/workflows/{id}` - Delete workflow (cascades)

### States & Transitions
- `GET /api/workflows/{id}/states` - List states
- `POST /api/workflows/{id}/states` - Create state
- `DELETE /api/workflows/states/{id}` - Delete state
- `POST /api/workflows/transitions` - Create transition
- `DELETE /api/workflows/transitions/{id}` - Delete transition

### Enrollments
- `GET /api/enrollments` - List enrollments (filter: `patient_id`, `outcome`)
- `GET /api/enrollments/{id}` - Get enrollment with current state
- `POST /api/enrollments` - Enroll patient
- `GET /api/enrollments/{id}/history` - State change history
- `POST /api/enrollments/{id}/transition` - Move to next state
- `POST /api/enrollments/{id}/complete` - Complete with outcome

## Configuration

Copy `programs.yml` to `/etc/survive/programs.yml`. Port: 8043.

## Running

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8043
```

## Testing

```bash
pytest tests/
```
