# kafka/tests/conftest.py
import hashlib
import os
import struct
import time
import uuid

import msgpack
import pytest
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient


@pytest.fixture
def bootstrap_servers() -> str:
    return os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


@pytest.fixture
def unique_topic() -> str:
    return f"test-spcc-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def unique_group_id() -> str:
    return f"test-cg-{uuid.uuid4().hex[:8]}"


def _emit_one_valid_message(bootstrap_servers, topic, payload=b"\x42" * 1024):
    p = Producer({"bootstrap.servers": bootstrap_servers, "message.max.bytes": 4_194_304})
    env = {
        "schema_version": 1,
        "message_id": "00000000-0000-4000-8000-000000000001",
        "producer_id": "pss-test",
        "timestamp_utc": int(time.time() * 1000),
        "candidate_type": "single_pulse",
        "payload_mode": "inline",
        "payload_size_bytes": len(payload),
        "checksum_sha256": hashlib.sha256(payload).hexdigest(),
        "spccl": {"beam_id": "beam-000", "scheduling_block_id": "sbi-test-0001"},
    }
    env_bytes = msgpack.packb(env, use_bin_type=True)
    value = struct.pack(">I", len(env_bytes)) + env_bytes + payload
    key = b"sbi-test-0001:beam-000"
    p.produce(topic, key=key, value=value)
    p.flush(5)
    return env, payload


def _wait_for_topic(bootstrap_servers, topic, timeout=10.0):
    admin = AdminClient({"bootstrap.servers": bootstrap_servers})
    deadline = time.time() + timeout
    while time.time() < deadline:
        md = admin.list_topics(timeout=2.0)
        if topic in md.topics and md.topics[topic].error is None:
            return
        time.sleep(0.2)
    raise RuntimeError(f"topic {topic} never appeared")
