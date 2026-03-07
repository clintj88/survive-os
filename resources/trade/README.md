# Trade & Barter Ledger - SURVIVE OS

Community trade and barter tracking with double-entry bookkeeping, exchange rates, market day coordination, and skills registry.

## Features

- **Double-Entry Ledger**: Record trades with give/receive sides, valued in labor hours
- **Exchange Rates**: Community-defined rates with labor hours as base unit
- **Trade History**: Per-person history, inter-party balances, volume statistics
- **Market Days**: Schedule trading events, post offers and wants
- **Skills Registry**: Track community skills as tradeable services

## Quick Start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8050
```

## API

| Endpoint | Description |
|---|---|
| `GET /health` | Health check |
| `GET/POST /api/trades` | List/create trades |
| `PATCH /api/trades/{id}/status` | Update trade status |
| `GET /api/trades/{id}/validate` | Validate trade balance |
| `GET/POST /api/rates` | List/create exchange rates |
| `GET /api/rates/current` | Current rates per commodity pair |
| `GET /api/rates/convert/{a}/{b}` | Convert between commodities |
| `GET /api/history/person/{name}` | Person trade history |
| `GET /api/history/balance/{a}/{b}` | Balance between parties |
| `GET /api/history/summary` | Trade volume statistics |
| `GET/POST /api/market` | List/create market days |
| `POST /api/market/{id}/listings` | Add market listing |
| `GET/POST /api/skills` | List/create skills |
| `GET /api/skills/search?q=` | Search skills |

## Configuration

Copy `trade.yml` to `/etc/survive/trade.yml`. Data stored at `/var/lib/survive/trade/`.

## Port

8050 (Resources / Inventory)
