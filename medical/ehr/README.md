# EHR-Lite - SURVIVE OS Electronic Health Records

Offline-first electronic health records for post-infrastructure medical care.

## Features

- **Patient Records**: Demographics, allergies, chronic conditions, search/filter
- **SOAP Visit Notes**: Structured clinical documentation with visit timeline
- **Vital Signs Tracking**: Time-series vitals with trend analysis and alerts
- **Wound Care Log**: Wound tracking with progress entries and photo documentation
- **Vaccination Records**: Immunization tracking with schedules and overdue alerts
- **Printable Summaries**: HTML patient summaries for transfer between communities
- **Audit Logging**: Full access/modification audit trail
- **SQLCipher Encryption**: Database encrypted at rest (production)

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8040
```

## Configuration

Config file: `/etc/survive/ehr.yml`

```yaml
database:
  path: /var/lib/survive/ehr/ehr.db
  key: your-encryption-key
server:
  host: 0.0.0.0
  port: 8040
lldap:
  url: ldap://localhost:3890
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| GET/POST | /api/patients | List/create patients |
| GET/PUT/DELETE | /api/patients/{id} | Patient CRUD |
| GET/POST | /api/patients/{id}/visits | Visit notes |
| GET/POST | /api/patients/{id}/vitals | Vital signs |
| GET | /api/patients/{id}/vitals/trends/{sign} | Vital trends |
| GET | /api/patients/{id}/vitals/alerts | Vital alerts |
| GET/POST | /api/patients/{id}/wounds | Wound records |
| POST | /api/patients/{id}/wounds/{id}/entries | Wound entries |
| GET/POST | /api/patients/{id}/vaccinations | Vaccinations |
| GET | /api/patients/{id}/vaccinations/overdue | Overdue vaccines |
| GET | /api/vaccinations/schedules | Vaccine schedules |
| GET | /api/vaccinations/coverage | Coverage report |
| GET | /api/patients/{id}/summary | Printable summary |

## Security

- All endpoints require `medical` role (X-User + X-Role headers)
- SQLCipher encryption at rest in production
- Full audit log of all access and modifications

## Testing

```bash
cd medical/ehr
python -m pytest tests/ -v
```

## Port

8040 (Medical, encrypted)
