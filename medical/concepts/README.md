# Concept Dictionary - SURVIVE OS Medical

Clinical concept dictionary for standardized medical terminology. Manages concepts, mappings to coding systems (ICD-10, SNOMED, LOINC), coded answers, and concept sets.

## Features

- Concept CRUD with soft-delete (retire/unretire)
- Datatypes: numeric, coded, text, boolean, date, datetime
- Concept classes: diagnosis, symptom, test, drug, procedure, finding, misc
- Mappings to ICD-10, SNOMED-CT, LOINC, and local codes
- Coded concept answers (e.g., blood type → A+, A-, B+, etc.)
- Concept sets for logical grouping (e.g., Vital Signs)
- Pre-seeded with common clinical concepts, ICD-10 mappings, and lab tests
- Optional SQLCipher encryption at rest
- Role-based access: requires `X-Role: medical` header

## API

### Concepts
- `GET /health` - Health check
- `GET /api/concepts` - List concepts (`include_retired` param)
- `GET /api/concepts/search` - Search (`q`, `class`, `source` params)
- `POST /api/concepts` - Create concept
- `GET /api/concepts/{id}` - Get concept with answers and mappings
- `PUT /api/concepts/{id}` - Update concept
- `POST /api/concepts/{id}/retire` - Retire concept
- `POST /api/concepts/{id}/unretire` - Unretire concept

### Answers
- `GET /api/concepts/{id}/answers` - List answers
- `POST /api/concepts/{id}/answers` - Add answer
- `DELETE /api/concepts/{id}/answers/{answer_id}` - Remove answer

### Mappings
- `GET /api/concepts/{id}/mappings` - List mappings
- `POST /api/concepts/{id}/mappings` - Create mapping
- `PUT /api/concepts/{id}/mappings/{mapping_id}` - Update mapping
- `DELETE /api/concepts/{id}/mappings/{mapping_id}` - Delete mapping

### Concept Sets
- `GET /api/sets` - List sets
- `POST /api/sets` - Create set
- `GET /api/sets/{id}` - Get set with members
- `PUT /api/sets/{id}` - Update set
- `DELETE /api/sets/{id}` - Delete set
- `GET /api/sets/{id}/members` - List members
- `POST /api/sets/{id}/members` - Add member
- `DELETE /api/sets/{id}/members/{member_id}` - Remove member

## Configuration

Copy `concepts.yml` to `/etc/survive/concepts.yml`. Port: 8041.

## Running

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8041
```

## Testing

```bash
pytest tests/
```
