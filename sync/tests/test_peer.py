"""Tests for PeerManager."""

import time

from sync.engine.peer import Peer, PeerManager


def test_add_static_peer():
    pm = PeerManager("node-1")
    peer = pm.add_static_peer("peer-1", "192.168.1.10", 8101, role="hub")

    assert peer.peer_id == "peer-1"
    assert peer.host == "192.168.1.10"
    assert peer.role == "hub"


def test_get_peer():
    pm = PeerManager("node-1")
    pm.add_static_peer("peer-1", "192.168.1.10", 8101)

    peer = pm.get_peer("peer-1")
    assert peer is not None
    assert peer.host == "192.168.1.10"

    assert pm.get_peer("nonexistent") is None


def test_update_peer():
    pm = PeerManager("node-1")
    pm.add_static_peer("peer-1", "192.168.1.10", 8101)

    updated = pm.update_peer("peer-1", role="gateway", name="Gateway A")
    assert updated is not None
    assert updated.role == "gateway"
    assert updated.name == "Gateway A"
    assert updated.online is True


def test_mark_seen():
    pm = PeerManager("node-1")
    pm.add_static_peer("peer-1", "192.168.1.10", 8101)

    pm.mark_seen("peer-1")
    peer = pm.get_peer("peer-1")
    assert peer is not None
    assert peer.online is True


def test_get_online_peers():
    pm = PeerManager("node-1")
    p1 = pm.add_static_peer("peer-1", "192.168.1.10", 8101)
    p1.online = True
    p1.last_seen = time.time()

    p2 = pm.add_static_peer("peer-2", "192.168.1.11", 8101)
    p2.online = True
    p2.last_seen = time.time() - 300  # Stale

    online = pm.get_online_peers()
    assert len(online) == 1
    assert online[0].peer_id == "peer-1"


def test_remove_peer():
    pm = PeerManager("node-1")
    pm.add_static_peer("peer-1", "192.168.1.10", 8101)
    assert pm.remove_peer("peer-1") is True
    assert pm.get_peer("peer-1") is None
    assert pm.remove_peer("nonexistent") is False


def test_get_all_peers():
    pm = PeerManager("node-1")
    pm.add_static_peer("peer-1", "192.168.1.10", 8101)
    pm.add_static_peer("peer-2", "192.168.1.11", 8101)
    assert len(pm.get_all_peers()) == 2


def test_peer_to_dict():
    peer = Peer(
        peer_id="peer-1",
        host="192.168.1.10",
        port=8101,
        role="hub",
        community="alpha",
    )
    d = peer.to_dict()
    assert d["peer_id"] == "peer-1"
    assert d["host"] == "192.168.1.10"
    assert d["role"] == "hub"
