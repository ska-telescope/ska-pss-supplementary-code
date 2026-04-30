from __future__ import annotations
import hashlib
import struct
from typing import Any, Mapping
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


_REQUIRED_FIELDS: dict[str, type] = {
    "schema_version": int,
    "message_id": str,
    "producer_id": str,
    "timestamp_utc": int,
    "candidate_type": str,
    "payload_mode": str,
    "payload_size_bytes": int,
    "checksum_sha256": str,
}


def validate(envelope: Mapping[str, Any], payload: bytes) -> None:
    for field, expected_type in _REQUIRED_FIELDS.items():
        if field not in envelope:
            raise ContractViolationError(f"missing required field: {field}")
        if not isinstance(envelope[field], expected_type) or isinstance(envelope[field], bool):
            raise ContractViolationError(
                f"{field} has wrong type: expected {expected_type.__name__}, "
                f"got {type(envelope[field]).__name__}"
            )

    if envelope["schema_version"] != 1:
        raise ContractViolationError(
            f"schema_version must be 1 (got {envelope['schema_version']})"
        )
    if envelope["candidate_type"] != "single_pulse":
        raise ContractViolationError(
            f"candidate_type must be 'single_pulse' (got {envelope['candidate_type']!r})"
        )
    if envelope["payload_mode"] not in {"inline", "claim_check"}:
        raise ContractViolationError(
            f"payload_mode must be 'inline' or 'claim_check' (got {envelope['payload_mode']!r})"
        )
    if envelope["timestamp_utc"] < 0 or envelope["timestamp_utc"] >= (1 << 64):
        raise ContractViolationError("timestamp_utc out of uint64 range")
    if envelope["payload_size_bytes"] < 0 or envelope["payload_size_bytes"] >= (1 << 32):
        raise ContractViolationError("payload_size_bytes out of uint32 range")

    if envelope["payload_mode"] == "inline":
        if len(payload) != envelope["payload_size_bytes"]:
            raise ContractViolationError(
                f"payload_size_bytes ({envelope['payload_size_bytes']}) "
                f"does not match actual payload length ({len(payload)})"
            )
        actual = hashlib.sha256(payload).hexdigest()
        if actual != envelope["checksum_sha256"]:
            raise ContractViolationError(
                f"checksum_sha256 mismatch (envelope={envelope['checksum_sha256']}, "
                f"actual={actual})"
            )
    else:  # claim_check
        for key in ("storage_uri", "storage_backend"):
            if not envelope.get(key):
                raise ContractViolationError(f"claim_check requires non-empty {key}")

    spccl = envelope.get("spccl")
    if not isinstance(spccl, dict):
        raise ContractViolationError("spccl must be a map")
    # TODO(AT4-2179): add field-level SPCCL validation once Cheetah/SDP confirm the field set.
