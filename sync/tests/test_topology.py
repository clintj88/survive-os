"""Tests for TopologyManager."""

from sync.engine.topology import NodeRole, TopologyManager


def test_hub_syncs_with_community_spokes():
    tm = TopologyManager("hub-1", NodeRole.HUB, "alpha")
    assert tm.should_sync_with("spoke-1", "spoke", "alpha") is True
    assert tm.should_sync_with("spoke-2", "spoke", "beta") is False


def test_hub_syncs_with_gateways():
    tm = TopologyManager("hub-1", NodeRole.HUB, "alpha")
    assert tm.should_sync_with("gw-1", "gateway", "alpha") is True
    assert tm.should_sync_with("gw-2", "gateway", "beta") is True


def test_spoke_only_syncs_with_own_hub():
    tm = TopologyManager("spoke-1", NodeRole.SPOKE, "alpha")
    assert tm.should_sync_with("hub-1", "hub", "alpha") is True
    assert tm.should_sync_with("hub-2", "hub", "beta") is False
    assert tm.should_sync_with("spoke-2", "spoke", "alpha") is False


def test_gateway_syncs_with_own_hub_and_remote():
    tm = TopologyManager("gw-1", NodeRole.GATEWAY, "alpha")
    assert tm.should_sync_with("hub-1", "hub", "alpha") is True
    assert tm.should_sync_with("hub-2", "hub", "beta") is True
    assert tm.should_sync_with("gw-2", "gateway", "beta") is True
    assert tm.should_sync_with("spoke-1", "spoke", "alpha") is False


def test_record_sync():
    tm = TopologyManager("hub-1", NodeRole.HUB, "alpha")
    tm.record_sync("spoke-1", {"node-1": 5})

    state = tm.get_sync_state("spoke-1")
    assert state.sync_count == 1
    assert state.last_vector_clock == {"node-1": 5}


def test_record_error():
    tm = TopologyManager("hub-1", NodeRole.HUB, "alpha")
    tm.record_error("spoke-1", "connection refused")

    state = tm.get_sync_state("spoke-1")
    assert state.errors == 1
    assert state.last_error == "connection refused"


def test_sync_summary():
    tm = TopologyManager("hub-1", NodeRole.HUB, "alpha")
    summary = tm.get_sync_summary()
    assert summary["node_id"] == "hub-1"
    assert summary["role"] == "hub"
    assert summary["community"] == "alpha"
