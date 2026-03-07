"""API routes for the BBS module."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query
from .sync import get_sync_status

router = APIRouter(prefix="/api")


class ThreadCreate(BaseModel):
    topic_id: int
    title: str
    author: str
    content: str  # first post content


class PostCreate(BaseModel):
    author: str
    content: str
    parent_id: Optional[int] = None


class PostUpdate(BaseModel):
    content: str


# --- Topics ---

@router.get("/topics")
def list_topics() -> list[dict]:
    return query(
        """SELECT t.id, t.name, t.slug, t.description, t.created_at,
                  COUNT(th.id) as thread_count
           FROM topics t
           LEFT JOIN threads th ON th.topic_id = t.id
           GROUP BY t.id
           ORDER BY t.name"""
    )


@router.get("/topics/{topic_id}")
def get_topic(topic_id: int) -> dict:
    results = query("SELECT id, name, slug, description, created_at FROM topics WHERE id = ?", (topic_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Topic not found")
    return results[0]


# --- Threads ---

@router.get("/topics/{topic_id}/threads")
def list_threads(topic_id: int) -> list[dict]:
    # Verify topic exists
    if not query("SELECT id FROM topics WHERE id = ?", (topic_id,)):
        raise HTTPException(status_code=404, detail="Topic not found")
    return query(
        """SELECT t.id, t.title, t.slug, t.author, t.pinned, t.locked,
                  t.created_at, t.updated_at,
                  COUNT(p.id) as post_count,
                  MAX(p.created_at) as last_post_at
           FROM threads t
           LEFT JOIN posts p ON p.thread_id = t.id
           WHERE t.topic_id = ?
           GROUP BY t.id
           ORDER BY t.pinned DESC, t.updated_at DESC""",
        (topic_id,),
    )


@router.get("/threads/{thread_id}")
def get_thread(thread_id: int) -> dict:
    results = query(
        """SELECT t.id, t.title, t.slug, t.author, t.topic_id, t.pinned,
                  t.locked, t.created_at, t.updated_at,
                  tp.name as topic_name, tp.slug as topic_slug
           FROM threads t
           JOIN topics tp ON tp.id = t.topic_id
           WHERE t.id = ?""",
        (thread_id,),
    )
    if not results:
        raise HTTPException(status_code=404, detail="Thread not found")
    return results[0]


@router.post("/threads", status_code=201)
def create_thread(thread: ThreadCreate) -> dict:
    if not query("SELECT id FROM topics WHERE id = ?", (thread.topic_id,)):
        raise HTTPException(status_code=400, detail="Topic not found")

    slug = thread.title.lower().replace(" ", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")

    thread_id = execute(
        """INSERT INTO threads (topic_id, title, slug, author)
           VALUES (?, ?, ?, ?)""",
        (thread.topic_id, thread.title, slug, thread.author),
    )

    # Create the first post
    execute(
        "INSERT INTO posts (thread_id, author, content) VALUES (?, ?, ?)",
        (thread_id, thread.author, thread.content),
    )

    return get_thread(thread_id)


# --- Posts ---

@router.get("/threads/{thread_id}/posts")
def list_posts(thread_id: int) -> list[dict]:
    if not query("SELECT id FROM threads WHERE id = ?", (thread_id,)):
        raise HTTPException(status_code=404, detail="Thread not found")
    return query(
        """SELECT id, thread_id, author, content, parent_id, created_at, updated_at
           FROM posts WHERE thread_id = ?
           ORDER BY created_at ASC""",
        (thread_id,),
    )


@router.post("/threads/{thread_id}/posts", status_code=201)
def create_post(thread_id: int, post: PostCreate) -> dict:
    thread = query("SELECT id, locked FROM threads WHERE id = ?", (thread_id,))
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    if thread[0]["locked"]:
        raise HTTPException(status_code=403, detail="Thread is locked")

    if post.parent_id is not None:
        parent = query(
            "SELECT id FROM posts WHERE id = ? AND thread_id = ?",
            (post.parent_id, thread_id),
        )
        if not parent:
            raise HTTPException(status_code=400, detail="Parent post not found in this thread")

    post_id = execute(
        "INSERT INTO posts (thread_id, author, content, parent_id) VALUES (?, ?, ?, ?)",
        (thread_id, post.author, post.content, post.parent_id),
    )

    # Update thread's updated_at
    execute(
        "UPDATE threads SET updated_at = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), thread_id),
    )

    results = query("SELECT * FROM posts WHERE id = ?", (post_id,))
    return dict(results[0])


@router.put("/posts/{post_id}")
def update_post(post_id: int, update: PostUpdate) -> dict:
    existing = query("SELECT id FROM posts WHERE id = ?", (post_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Post not found")

    execute(
        "UPDATE posts SET content = ?, updated_at = ? WHERE id = ?",
        (update.content, datetime.now(timezone.utc).isoformat(), post_id),
    )
    results = query("SELECT * FROM posts WHERE id = ?", (post_id,))
    return dict(results[0])


@router.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: int) -> None:
    existing = query("SELECT id FROM posts WHERE id = ?", (post_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Post not found")
    execute("DELETE FROM posts WHERE id = ?", (post_id,))


# --- Search ---

@router.get("/search")
def search_posts(q: str = Query(..., min_length=1)) -> list[dict]:
    return query(
        """SELECT p.id, p.thread_id, p.author, p.content, p.created_at,
                  t.title as thread_title, t.slug as thread_slug,
                  tp.name as topic_name
           FROM posts_fts
           JOIN posts p ON p.id = posts_fts.rowid
           JOIN threads t ON t.id = p.thread_id
           JOIN topics tp ON tp.id = t.topic_id
           WHERE posts_fts MATCH ?
           ORDER BY rank""",
        (q,),
    )


# --- Sync ---

@router.get("/sync/status")
def sync_status() -> dict:
    return get_sync_status()
