# Seed Bank Management - SURVIVE OS

Manage seed inventories, track germination rates, predict viability, monitor genetic diversity, and coordinate seed exchanges between communities.

## Features

- **Seed Inventory**: Track seed lots with ledger-style deposits/withdrawals and low-stock alerts
- **Germination Tracking**: Record germination tests and view historical rates per variety
- **Viability Prediction**: Species-specific decay curves adjusted for storage conditions
- **Genetic Diversity**: Monitor source diversity per crop with configurable thresholds
- **Seed Exchange**: List seeds for cross-community trading via Redis pub/sub

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8030
```

## Configuration

Copy `seed-bank.yml` to `/etc/survive/seed-bank.yml` and adjust as needed.

## API Endpoints

- `GET /health` - Health check
- `GET /api/inventory/lots` - List seed lots
- `POST /api/inventory/lots` - Create seed lot
- `POST /api/inventory/lots/{id}/ledger` - Deposit/withdraw seeds
- `GET /api/germination/tests` - List germination tests
- `POST /api/germination/tests` - Record germination test
- `GET /api/viability/dashboard` - Viability status for all lots
- `GET /api/diversity/scores` - Diversity scores per species
- `GET /api/exchange/listings` - Exchange listings

## Port

8030 (Agriculture)
