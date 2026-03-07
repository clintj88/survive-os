# Ham Radio Integration - SURVIVE OS

Amateur radio integration module for post-infrastructure communication. Provides Winlink email over radio via Pat, HF keyboard messaging via JS8Call, a frequency database, and a contact scheduler.

## Features

- **Winlink/Pat**: Compose, send, and receive email over amateur radio
- **JS8Call**: HF keyboard messaging and activity monitoring
- **Frequency Database**: Pre-seeded with emergency/survival frequencies
- **Contact Scheduler**: Schedule nets and radio contacts

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/winlink/messages` | List Winlink messages |
| POST | `/api/winlink/compose` | Compose Winlink message |
| POST | `/api/winlink/send` | Send queued messages |
| POST | `/api/winlink/receive` | Poll for new messages |
| GET | `/api/js8call/status` | JS8Call connection status |
| POST | `/api/js8call/send` | Send JS8Call message |
| GET | `/api/js8call/activity` | Get band/call activity |
| GET | `/api/js8call/messages` | List JS8Call message log |
| GET | `/api/frequencies` | List frequencies (filter: band, mode, usage) |
| POST | `/api/frequencies` | Add frequency |
| PUT | `/api/frequencies/{id}` | Update frequency |
| DELETE | `/api/frequencies/{id}` | Delete frequency |
| GET | `/api/contacts` | List scheduled contacts |
| POST | `/api/contacts` | Create scheduled contact |
| PUT | `/api/contacts/{id}` | Update contact |
| DELETE | `/api/contacts/{id}` | Delete contact |

## Configuration

Copy `ham-radio.yml` to `/etc/survive/ham-radio.yml` and adjust settings.

## Running

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8010
```

## Testing

```bash
pip install pytest httpx
pytest tests/
```

## Port

8010 (Comms subsystem)
