import struct
import pytest
import msgpack
from pss_sdp_consumer.contract import parse_value, EnvelopeDecodeError

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
