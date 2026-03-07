"""UUID v7 (time-ordered) and UUID v4 generators for record IDs."""

import os
import time
import uuid


def uuid7() -> str:
    """Generate a UUID v7 (time-ordered, random) as a hex string.

    Layout (RFC 9562):
      - 48 bits: Unix timestamp in milliseconds
      -  4 bits: version (0b0111)
      - 12 bits: rand_a
      -  2 bits: variant (0b10)
      - 62 bits: rand_b
    """
    timestamp_ms = int(time.time() * 1000)
    rand_bytes = os.urandom(10)

    # 48-bit timestamp
    ts_high = (timestamp_ms >> 16) & 0xFFFFFFFF
    ts_low = timestamp_ms & 0xFFFF

    # rand_a (12 bits) from rand_bytes[0:2]
    rand_a = int.from_bytes(rand_bytes[0:2], "big") & 0x0FFF

    # rand_b (62 bits) from rand_bytes[2:10]
    rand_b = int.from_bytes(rand_bytes[2:10], "big") & 0x3FFFFFFFFFFFFFFF

    # Assemble 128-bit value
    value = (ts_high << 96) | (ts_low << 80) | (0x7 << 76) | (rand_a << 64) | (0b10 << 62) | rand_b

    return uuid.UUID(int=value).hex


def uuid4() -> str:
    """Generate a standard UUID v4 as a hex string."""
    return uuid.uuid4().hex


def generate_id() -> str:
    """Generate a new record ID (UUID v7 by default)."""
    return uuid7()
