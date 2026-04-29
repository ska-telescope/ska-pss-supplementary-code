# kafka/tests/test_consumer_roundtrip.py
import threading
import time
import logging
import pytest

from pss_sdp_consumer.config import ConsumerConfig
from pss_sdp_consumer.consumer import Consumer

from conftest import _emit_one_valid_message, _wait_for_topic

pytestmark = pytest.mark.integration


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
