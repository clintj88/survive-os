"""Tests for vector clock implementation."""

from shared.db.vector_clock import VectorClock


def test_increment():
    vc = VectorClock()
    assert vc.increment("a") == 1
    assert vc.increment("a") == 2
    assert vc.get("a") == 2
    assert vc.get("b") == 0


def test_merge():
    vc1 = VectorClock({"a": 2, "b": 1})
    vc2 = VectorClock({"a": 1, "b": 3, "c": 1})
    merged = vc1.merge(vc2)
    assert merged.get("a") == 2
    assert merged.get("b") == 3
    assert merged.get("c") == 1


def test_ordering_less_than():
    vc1 = VectorClock({"a": 1})
    vc2 = VectorClock({"a": 2})
    assert vc1 < vc2
    assert vc1 <= vc2
    assert not vc1 > vc2


def test_ordering_equal():
    vc1 = VectorClock({"a": 1, "b": 2})
    vc2 = VectorClock({"a": 1, "b": 2})
    assert vc1 == vc2
    assert vc1 <= vc2
    assert vc1 >= vc2
    assert not vc1 < vc2


def test_concurrent():
    vc1 = VectorClock({"a": 2, "b": 1})
    vc2 = VectorClock({"a": 1, "b": 2})
    assert vc1.is_concurrent(vc2)
    assert not vc1 < vc2
    assert not vc1 > vc2


def test_json_roundtrip():
    vc = VectorClock({"node-1": 5, "node-2": 3})
    json_str = vc.to_json()
    restored = VectorClock.from_json(json_str)
    assert vc == restored


def test_dict_roundtrip():
    vc = VectorClock({"a": 1})
    d = vc.to_dict()
    assert d == {"a": 1}
    restored = VectorClock.from_dict(d)
    assert vc == restored


def test_empty_clocks_equal():
    assert VectorClock() == VectorClock()
    assert VectorClock() == VectorClock({"a": 0})
