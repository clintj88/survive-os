"""Tests for UUID generation."""

import time

from shared.db.ids import generate_id, uuid4, uuid7


def test_uuid7_format():
    uid = uuid7()
    assert len(uid) == 32
    assert all(c in "0123456789abcdef" for c in uid)


def test_uuid7_version_bits():
    uid = uuid7()
    # Version nibble is at position 12 (0-indexed in hex string)
    assert uid[12] == "7"


def test_uuid7_time_ordered():
    """IDs generated across different milliseconds should sort chronologically."""
    ids = []
    for _ in range(5):
        ids.append(uuid7())
        time.sleep(0.002)  # 2ms gap ensures different timestamp
    assert ids == sorted(ids)


def test_uuid7_uniqueness():
    ids = {uuid7() for _ in range(1000)}
    assert len(ids) == 1000


def test_uuid4_format():
    uid = uuid4()
    assert len(uid) == 32
    assert all(c in "0123456789abcdef" for c in uid)


def test_uuid4_version_bits():
    uid = uuid4()
    assert uid[12] == "4"


def test_generate_id_returns_uuid7():
    uid = generate_id()
    assert uid[12] == "7"
