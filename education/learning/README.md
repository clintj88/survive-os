# Education & Learning - SURVIVE OS

Apprenticeship tracking, lesson plans, children's education, and external content integration for post-infrastructure communities.

## Features

- **Apprenticeship Tracking**: Enroll apprentices in trades, track skill progress with checklists, certify completion
- **Lesson Plans & Curriculum**: Searchable lesson plans by subject and age group, curriculum guides
- **Children's Education**: Math quizzes, reading exercises, science activities with progress tracking
- **External Content**: Integration with Kiwix (offline Wikipedia), OpenStax textbooks, Project Gutenberg

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8090
```

## API Endpoints

- `GET /health` - Health check
- `GET/POST /api/apprentices` - Apprenticeship management
- `PUT /api/apprentices/{id}/skills/{skill_id}` - Update skill status
- `GET/POST /api/lessons` - Lesson plans
- `GET/POST /api/curricula` - Curriculum guides
- `GET /api/children/math` - Generate math problems
- `POST /api/children/math/submit` - Submit quiz answers
- `GET /api/children/reading` - Reading exercises
- `GET /api/children/science` - Science activities
- `GET /api/external/resources` - External content status

## Configuration

Copy `learning.yml` to `/etc/survive/learning.yml` and adjust as needed.

## Port

8090 (Education)
