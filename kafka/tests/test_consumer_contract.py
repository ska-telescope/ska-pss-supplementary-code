import hashlib
import struct
import pytest
import msgpack
from pss_sdp_consumer.contract import (
    ContractViolationError,
    EnvelopeDecodeError,
    parse_value,
    validate,
)

pytestmark = pytest.mark.unit


def _frame(env: dict, payload: bytes) -> bytes:
    env_bytes = msgpack.packb(env, use_bin_type=True)
    return struct.pack(">I", len(env_bytes)) + env_bytes + payload


def test_parse_value_round_trips_envelope_and_payload():
    env = {"schema_version": 1, "message_id": "m"}
    payload = b"\x00\x01\x02\x03"
    out_env, out_payload = parse_value(_frame(env, payload))
    assert out_env == env
    assert out_payload == payload


def test_parse_value_rejects_short_buffer():
    with pytest.raises(EnvelopeDecodeError):
        parse_value(b"\x00\x00")


def test_parse_value_rejects_oversized_envelope_length():
    bogus = struct.pack(">I", 999_999) + b"x"
    with pytest.raises(EnvelopeDecodeError):
        parse_value(bogus)


def test_parse_value_rejects_malformed_msgpack():
    bad = struct.pack(">I", 3) + b"\xc1\xc1\xc1" + b"payload"
    with pytest.raises(EnvelopeDecodeError):
        parse_value(bad)


def _good_envelope(payload: bytes) -> dict:
    return {
        "schema_version": 1,
        "message_id": "00000000-0000-4000-8000-000000000000",
        "producer_id": "pss-test-node-01",
        "timestamp_utc": 1_700_000_000_000,
        "candidate_type": "single_pulse",
        "payload_mode": "inline",
        "payload_size_bytes": len(payload),
        "checksum_sha256": hashlib.sha256(payload).hexdigest(),
        "spccl": {"beam_id": "beam-000", "scheduling_block_id": "sbi-test-0001"},
    }


def test_validate_accepts_good_inline_message():
    payload = b"\x00" * 1024
    validate(_good_envelope(payload), payload)


def test_validate_rejects_missing_field():
    payload = b""
    env = _good_envelope(payload)
    del env["message_id"]
    with pytest.raises(ContractViolationError, match="message_id"):
        validate(env, payload)


def test_validate_rejects_wrong_schema_version():
    payload = b""
    env = _good_envelope(payload)
    env["schema_version"] = 2
    with pytest.raises(ContractViolationError, match="schema_version"):
        validate(env, payload)


def test_validate_rejects_payload_size_mismatch():
    payload = b"abc"
    env = _good_envelope(payload)
    env["payload_size_bytes"] = 99
    with pytest.raises(ContractViolationError, match="payload_size_bytes"):
        validate(env, payload)


def test_validate_rejects_checksum_mismatch():
    payload = b"abc"
    env = _good_envelope(payload)
    env["checksum_sha256"] = "0" * 64
    with pytest.raises(ContractViolationError, match="checksum_sha256"):
        validate(env, payload)


def test_validate_claim_check_requires_storage_fields():
    env = _good_envelope(b"")
    env["payload_mode"] = "claim_check"
    env["payload_size_bytes"] = 2_500_000
    with pytest.raises(ContractViolationError, match="storage_uri"):
        validate(env, b"")
    env["storage_uri"] = "s3://bucket/key"
    env["storage_backend"] = "ceph_rgw"
    validate(env, b"")  # passes; payload bytes not fetched
