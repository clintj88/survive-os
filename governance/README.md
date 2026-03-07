# SURVIVE OS - Governance Module

Community governance tools: census, voting, resource allocation, treaties,
dispute resolution, duty scheduling, community journal, civil registry,
and community calendar.

## Port: 8070

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8070
```

## API Endpoints

- `GET /health` - Health check
- `/api/census/*` - Census & population management
- `/api/voting/*` - Community voting & ballots
- `/api/resources/*` - Resource allocation & rationing
- `/api/treaties/*` - Treaties & agreements
- `/api/disputes/*` - Dispute resolution
- `/api/duties/*` - Duty scheduling
- `/api/journal/*` - Community journal
- `/api/registry/*` - Civil registry (births, deaths, marriages)
- `/api/calendar/*` - Community calendar

## Configuration

Copy `governance.yml` to `/etc/survive/governance.yml`.

## Tests

```bash
pytest tests/
```
