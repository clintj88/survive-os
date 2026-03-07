# SURVIVE OS Knowledge Base

Offline-first survival knowledge base for post-infrastructure communities. Provides searchable articles on first aid, water purification, shelter building, food preservation, navigation, and radio communications.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run with default in-memory database
cd education/knowledge-base
uvicorn app.main:app --port 8090

# Seed with initial content
python -m seed.seed_data
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (`{status, version}`) |
| GET | `/api/categories` | List all categories |
| GET | `/api/articles?category=slug` | List articles, optionally by category |
| GET | `/api/articles/{id}` | Get full article content |
| POST | `/api/articles` | Create article (admin) |
| PUT | `/api/articles/{id}` | Update article (admin) |
| GET | `/api/search?q=term` | Full-text search |

## Configuration

Copy `education.yml` to `/etc/survive/education.yml` and adjust:

```yaml
database:
  path: /var/lib/survive/education/knowledge.db
server:
  host: 0.0.0.0
  port: 8090
```

## Adding Content

Create articles via the API:

```bash
curl -X POST http://localhost:8090/api/articles \
  -H "Content-Type: application/json" \
  -d '{"title":"My Article","category_id":1,"content":"# Heading\n\nContent here.","summary":"Brief description"}'
```

Or add seed data in `seed/seed_data.py` and re-run the seed script.

## Testing

```bash
pip install pytest httpx
pytest tests/
```

## Architecture

- **Backend**: FastAPI (Python 3.11+)
- **Database**: SQLite with FTS5 for full-text search
- **Frontend**: Plain HTML/CSS/JS with client-side markdown rendering
- **Port**: 8090
- **Data**: `/var/lib/survive/education/`
- **Config**: `/etc/survive/education.yml`
