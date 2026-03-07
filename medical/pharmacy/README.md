# Pharmacy - SURVIVE OS Medical Module

Medication management for post-infrastructure communities. Tracks inventory, prescriptions, drug interactions, natural medicine references, and dosage calculations.

## Features

- **Pharmacy Inventory**: Medication CRUD, lot tracking, FIFO dispensing by expiration
- **Expiration Alerts**: Configurable alerts at 30/60/90 days, expired medication flagging
- **Prescription Tracking**: Patient prescriptions, dispensing log, refill tracking
- **Drug Interaction Checker**: 50+ pre-seeded interaction pairs with severity levels
- **Natural Medicine Reference**: 15+ herbal remedies with preparation, dosage, contraindications
- **Dosage Calculator**: Weight-based pediatric dosing with adult reference doses

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8040
```

## Configuration

Config file: `/etc/survive/pharmacy.yml`

Uses SQLCipher for encryption at rest in production. Falls back to standard SQLite for development/testing.

## API Endpoints

- `GET /health` - Health check
- `GET/POST /api/inventory/medications` - Medication CRUD
- `GET/POST /api/inventory/lots` - Inventory lot management
- `POST /api/inventory/dispense` - Dispense medication (FIFO)
- `GET /api/inventory/expiring?days=90` - Expiring medications
- `GET /api/inventory/expired` - Expired medications
- `GET/POST /api/prescriptions` - Prescription management
- `GET /api/prescriptions/patient/{id}/active` - Active prescriptions
- `POST /api/interactions/check` - Check drug interactions
- `POST /api/interactions/check-patient` - Check against patient's meds
- `GET/POST /api/natural` - Natural medicine reference
- `POST /api/dosage/calculate` - Calculate dose by weight/age
- `GET /api/dosage/rules` - List dosing rules

## Testing

```bash
pip install pytest httpx
cd medical/pharmacy
python -m pytest tests/ -v
```

## Port

8040 (Medical module)
