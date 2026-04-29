from __future__ import annotations
import struct
from typing import Any
import msgpack


class EnvelopeDecodeError(ValueError):
    """Raised when a Kafka message value cannot be split or msgpack-decoded."""


class ContractViolationError(ValueError):
    """Raised when a decoded envelope does not satisfy AT4-2179 section 2."""


def parse_value(buf: bytes) -> tuple[dict[str, Any], bytes]:
    if len(buf) < 4:
        raise EnvelopeDecodeError(f"buffer too short for length prefix: {len(buf)} bytes")
    env_len = struct.unpack(">I", buf[:4])[0]
    if env_len > len(buf) - 4:
        raise EnvelopeDecodeError(
            f"envelope length {env_len} exceeds remaining buffer {len(buf) - 4}"
        )
    try:
        envelope = msgpack.unpackb(buf[4 : 4 + env_len], raw=False)
    except Exception as e:
        raise EnvelopeDecodeError(f"msgpack decode failed: {e}") from e
    if not isinstance(envelope, dict):
        raise EnvelopeDecodeError(f"envelope is not a map (got {type(envelope).__name__})")
    payload = buf[4 + env_len :]
    return envelope, payload
