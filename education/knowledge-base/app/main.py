"""Knowledge Base API - SURVIVE OS Education Module."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import load_config
from .database import execute, init_db, query, set_db_path

config = load_config()
VERSION = config["version"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    set_db_path(config["database"]["path"])
    init_db()
    yield


app = FastAPI(title="SURVIVE OS Knowledge Base", version=VERSION, lifespan=lifespan)


class ArticleCreate(BaseModel):
    title: str
    category_id: int
    content: str
    summary: str = ""
    author: str = "system"


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


@app.get("/api/categories")
def list_categories() -> list[dict]:
    return query("SELECT id, name, slug, description FROM categories ORDER BY name")


@app.get("/api/articles")
def list_articles(category: Optional[str] = Query(None)) -> list[dict]:
    if category:
        return query(
            """SELECT a.id, a.title, a.slug, a.summary, a.author,
                      a.created_at, a.updated_at, c.name as category, c.slug as category_slug
               FROM articles a JOIN categories c ON a.category_id = c.id
               WHERE c.slug = ? ORDER BY a.title""",
            (category,),
        )
    return query(
        """SELECT a.id, a.title, a.slug, a.summary, a.author,
                  a.created_at, a.updated_at, c.name as category, c.slug as category_slug
           FROM articles a JOIN categories c ON a.category_id = c.id
           ORDER BY a.title"""
    )


@app.get("/api/articles/{article_id}")
def get_article(article_id: int) -> dict:
    results = query(
        """SELECT a.id, a.title, a.slug, a.content, a.summary, a.author,
                  a.created_at, a.updated_at, c.name as category, c.slug as category_slug
           FROM articles a JOIN categories c ON a.category_id = c.id
           WHERE a.id = ?""",
        (article_id,),
    )
    if not results:
        raise HTTPException(status_code=404, detail="Article not found")
    return results[0]


@app.post("/api/articles", status_code=201)
def create_article(article: ArticleCreate) -> dict:
    # Verify category exists
    cats = query("SELECT id FROM categories WHERE id = ?", (article.category_id,))
    if not cats:
        raise HTTPException(status_code=400, detail="Category not found")

    slug = article.title.lower().replace(" ", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")

    article_id = execute(
        """INSERT INTO articles (title, slug, category_id, content, summary, author)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (article.title, slug, article.category_id, article.content, article.summary, article.author),
    )
    return get_article(article_id)


@app.put("/api/articles/{article_id}")
def update_article(article_id: int, article: ArticleUpdate) -> dict:
    existing = query("SELECT id FROM articles WHERE id = ?", (article_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Article not found")

    updates: list[str] = []
    params: list = []
    if article.title is not None:
        updates.append("title = ?")
        params.append(article.title)
    if article.content is not None:
        updates.append("content = ?")
        params.append(article.content)
    if article.summary is not None:
        updates.append("summary = ?")
        params.append(article.summary)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.append(article_id)

    execute(f"UPDATE articles SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_article(article_id)


@app.get("/api/search")
def search_articles(q: str = Query(..., min_length=1)) -> list[dict]:
    return query(
        """SELECT a.id, a.title, a.slug, a.summary, a.author,
                  a.created_at, a.updated_at, c.name as category, c.slug as category_slug,
                  snippet(articles_fts, 1, '<mark>', '</mark>', '...', 32) as snippet
           FROM articles_fts
           JOIN articles a ON a.id = articles_fts.rowid
           JOIN categories c ON a.category_id = c.id
           WHERE articles_fts MATCH ?
           ORDER BY rank""",
        (q,),
    )


# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
