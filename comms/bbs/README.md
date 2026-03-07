# SURVIVE OS Community BBS

Community bulletin board system with topics, threaded replies, and offline-first CRDT sync.

## Features

- Topic-based message board (General, Trade, Security, Agriculture, Medical, etc.)
- Threaded replies with nested post support
- Full-text search across all posts
- Automerge CRDT sync for offline-first operation
- User authentication against LLDAP via SSSD/PAM

## API

- `GET /health` - Health check
- `GET /api/topics` - List topics
- `GET /api/topics/{id}` - Get topic
- `GET /api/topics/{id}/threads` - List threads in topic
- `POST /api/threads` - Create thread
- `GET /api/threads/{id}` - Get thread
- `GET /api/threads/{id}/posts` - List posts in thread
- `POST /api/threads/{id}/posts` - Create post/reply
- `PUT /api/posts/{id}` - Update post
- `DELETE /api/posts/{id}` - Delete post
- `GET /api/search?q=` - Search posts
- `GET /api/sync/status` - Sync status

## Configuration

Copy `bbs.yml` to `/etc/survive/bbs.yml`.

## Running

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8010
```

## Testing

```bash
pytest tests/
```
