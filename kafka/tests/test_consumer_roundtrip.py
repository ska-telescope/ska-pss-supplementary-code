# kafka/tests/test_consumer_roundtrip.py
import hashlib
import struct
import threading
import time
import logging
import pytest
import msgpack
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient

from pss_sdp_consumer.config import ConsumerConfig
from pss_sdp_consumer.consumer import Consumer

pytestmark = pytest.mark.integration


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


def test_consumes_validates_and_commits(bootstrap_servers, unique_topic, unique_group_id, caplog):
    captured = []

    def handler(env, payload):
        captured.append((dict(env), bytes(payload)))

    expected_env, expected_payload = _emit_one_valid_message(bootstrap_servers, unique_topic)
    _wait_for_topic(bootstrap_servers, unique_topic)

    cfg = ConsumerConfig(
        topic=unique_topic,
        handler="pss_sdp_consumer.handlers:log_handler",  # overridden below
        metrics_interval_s=1,
        client_conf={
            "bootstrap.servers": bootstrap_servers,
            "group.id": unique_group_id,
            "enable.auto.commit": "false",
            "auto.offset.reset": "earliest",
        },
    )
    consumer = Consumer(cfg, handler=handler)

    t = threading.Thread(target=consumer.run, daemon=True)
    with caplog.at_level(logging.INFO):
        t.start()
        deadline = time.time() + 15.0
        while time.time() < deadline and not captured:
            time.sleep(0.1)
        consumer.stop()
        t.join(timeout=10.0)

    assert len(captured) == 1
    env, payload = captured[0]
    assert env["message_id"] == expected_env["message_id"]
    assert payload == expected_payload
    assert any("throughput summary" in r.getMessage() for r in caplog.records)
