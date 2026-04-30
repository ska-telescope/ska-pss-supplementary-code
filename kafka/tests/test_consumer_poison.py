# kafka/tests/test_consumer_poison.py
import logging
import struct
import threading
import time
import pytest
from confluent_kafka import Producer

from pss_sdp_consumer.config import ConsumerConfig
from pss_sdp_consumer.consumer import Consumer
from _helpers import _emit_one_valid_message, _wait_for_topic

pytestmark = pytest.mark.integration


def test_skips_poison_and_commits_then_processes_next(
    bootstrap_servers, unique_topic, unique_group_id, caplog
):
    # Emit a poison message (truncated envelope) before the valid one.
    p = Producer({"bootstrap.servers": bootstrap_servers, "message.max.bytes": 4_194_304})
    p.produce(unique_topic, key=b"poison", value=struct.pack(">I", 999_999) + b"x")
    p.flush(5)
    expected_env, expected_payload = _emit_one_valid_message(bootstrap_servers, unique_topic)
    _wait_for_topic(bootstrap_servers, unique_topic)

    captured = []

    def handler(env, payload):
        captured.append((dict(env), bytes(payload)))

    cfg = ConsumerConfig(
        topic=unique_topic,
        handler="pss_sdp_consumer.handlers:log_handler",
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
    with caplog.at_level(logging.ERROR, logger="pss_sdp_consumer.consumer"):
        t.start()
        deadline = time.time() + 20.0
        while time.time() < deadline and not captured:
            time.sleep(0.1)
        consumer.stop()
        t.join(timeout=10.0)

    assert len(captured) == 1
    assert captured[0][0]["message_id"] == expected_env["message_id"]
    assert any("poison message" in r.getMessage() for r in caplog.records)
