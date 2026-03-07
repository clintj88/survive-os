"""SURVIVE OS CRDT Sync Engine — FastAPI service."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .config import load_config
from ..engine.document import SyncDocument
from ..engine.merge import MergeEngine
from ..engine.peer import PeerManager
from ..engine.store import DocumentStore
from ..engine.topology import NodeRole, TopologyManager

config = load_config()
VERSION = config["version"]

# Initialize node ID
node_id = config["node"]["id"] or str(uuid.uuid4())

# Core components
store = DocumentStore(
    db_path=config["database"]["path"],
    storage_path=config["storage"]["path"],
)
merge_engine = MergeEngine()
topology = TopologyManager(
    node_id=node_id,
    role=NodeRole(config["node"]["role"]),
    community=config["node"]["community"],
)
peer_manager = PeerManager(
    node_id=node_id,
    mdns_name=config["transport"]["tcp"]["mdns_name"],
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    store.init()

    # Add static peers from config
    for peer_cfg in config["discovery"].get("static_peers", []):
        peer_manager.add_static_peer(
            peer_id=peer_cfg.get("id", str(uuid.uuid4())),
            host=peer_cfg["host"],
            port=peer_cfg.get("port", 8101),
        )

    # Start mDNS discovery if enabled
    if config["discovery"]["mdns_enabled"]:
        await peer_manager.start_mdns_discovery()

    yield

    await peer_manager.stop_mdns_discovery()
    store.close()


app = FastAPI(title="SURVIVE OS Sync Engine", version=VERSION, lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": VERSION}


# --- Document endpoints ---

class DocumentCreate(BaseModel):
    doc_type: str
    data: dict[str, Any] = {}


class DocumentUpdate(BaseModel):
    changes: dict[str, Any]


@app.post("/api/documents")
def create_document(body: DocumentCreate) -> dict[str, Any]:
    doc = SyncDocument(
        doc_type=body.doc_type,
        node_id=node_id,
        data=body.data,
    )
    doc.vector_clock[node_id] = 1
    doc.history.append({
        "node_id": node_id,
        "seq": 1,
        "timestamp": doc.created_at,
        "changes": body.data,
    })
    store.save(doc)
    return doc.to_dict()


@app.get("/api/documents/{doc_id}")
def get_document(doc_id: str) -> dict[str, Any]:
    doc = store.load(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc.to_dict()


@app.patch("/api/documents/{doc_id}")
def update_document(doc_id: str, body: DocumentUpdate) -> dict[str, Any]:
    doc = store.load(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.node_id = node_id
    doc.update(body.changes)
    store.save(doc)
    return doc.to_dict()


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str) -> dict[str, str]:
    store.delete(doc_id)
    return {"status": "deleted"}


@app.get("/api/documents")
def list_documents(doc_type: str | None = None, since: float | None = None) -> list[dict[str, Any]]:
    if doc_type:
        return store.list_by_type(doc_type)
    if since is not None:
        return store.list_modified_since(since)
    return store.list_all()


# --- Sync endpoints ---

class SyncRequest(BaseModel):
    sender_id: str
    sender_community: str = "default"
    vector_clocks: dict[str, dict[str, int]] = {}


@app.post("/api/sync/handshake")
def sync_handshake(body: SyncRequest) -> dict[str, Any]:
    """Receive a sync handshake and return documents the sender needs."""
    offered_docs: list[dict[str, Any]] = []

    for doc_meta in store.list_all():
        doc = store.load(doc_meta["doc_id"])
        if doc is None:
            continue
        remote_clock = body.vector_clocks.get(doc.doc_id, {})
        changes = doc.get_changes_since(remote_clock)
        if changes:
            offered_docs.append(doc.to_dict())

    return {
        "node_id": node_id,
        "community": topology.community,
        "documents": offered_docs,
    }


class SyncPush(BaseModel):
    sender_id: str
    documents: list[dict[str, Any]]


@app.post("/api/sync/push")
def sync_push(body: SyncPush) -> dict[str, Any]:
    """Receive documents from a peer and merge them."""
    results = []
    for doc_dict in body.documents:
        doc_id = doc_dict.get("doc_id", "")
        local = store.load(doc_id)

        merged_doc, result = merge_engine.merge_from_snapshot(local, doc_dict)
        if result.merged:
            store.save(merged_doc)

        results.append({
            "doc_id": doc_id,
            "merged": result.merged,
            "conflicts": result.conflicts,
            "changes_applied": result.changes_applied,
        })

    topology.record_sync(
        body.sender_id,
        {r["doc_id"]: {} for r in results if r["merged"]},
    )

    return {"node_id": node_id, "results": results}


# --- Peer endpoints ---

@app.get("/api/peers")
def list_peers() -> list[dict[str, Any]]:
    return [p.to_dict() for p in peer_manager.get_all_peers()]


@app.get("/api/peers/online")
def list_online_peers() -> list[dict[str, Any]]:
    return [p.to_dict() for p in peer_manager.get_online_peers()]


class PeerAdd(BaseModel):
    peer_id: str = ""
    host: str
    port: int = 8101
    role: str = "spoke"
    community: str = "default"
    name: str = ""


@app.post("/api/peers")
def add_peer(body: PeerAdd) -> dict[str, Any]:
    peer_id = body.peer_id or str(uuid.uuid4())
    peer = peer_manager.add_static_peer(
        peer_id=peer_id,
        host=body.host,
        port=body.port,
        role=body.role,
        community=body.community,
        name=body.name,
    )
    return peer.to_dict()


@app.delete("/api/peers/{peer_id}")
def remove_peer(peer_id: str) -> dict[str, str]:
    peer_manager.remove_peer(peer_id)
    return {"status": "removed"}


# --- Status endpoints ---

@app.get("/api/status")
def sync_status() -> dict[str, Any]:
    return {
        "node_id": node_id,
        "role": topology.role.value,
        "community": topology.community,
        "document_count": store.count(),
        "peers_online": len(peer_manager.get_online_peers()),
        "peers_total": len(peer_manager.get_all_peers()),
        "topology": topology.get_sync_summary(),
    }
