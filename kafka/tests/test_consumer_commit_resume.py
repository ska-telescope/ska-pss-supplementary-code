# kafka/tests/test_consumer_commit_resume.py
import threading
import time
import pytest

from pss_sdp_consumer.consumer import Consumer

from _helpers import _emit_one_valid_message, _wait_for_topic

pytestmark = pytest.mark.integration


def test_committed_offset_survives_restart(
    bootstrap_servers, unique_topic, unique_group_id, make_consumer_config
):
    # Three distinguishable payloads on the same topic.
    expected = []
    for i in range(3):
        env, payload = _emit_one_valid_message(
            bootstrap_servers, unique_topic, payload=bytes([i + 1]) * 1024
        )
        expected.append(payload)
    _wait_for_topic(bootstrap_servers, unique_topic)

    # Run 1: handler stops the consumer in-band after exactly two messages.
    # Stopping from inside the handler guarantees the commit for message #2
    # has completed (commit is the next statement after the handler call)
    # before the run loop exits.
    captured_1 = []
    consumer_1_holder = {}

    def handler_1(env, payload):
        captured_1.append(bytes(payload))
        if len(captured_1) == 2:
            consumer_1_holder["consumer"].stop()

    consumer_1 = Consumer(
        make_consumer_config(unique_topic, unique_group_id),
        handler=handler_1,
    )
    consumer_1_holder["consumer"] = consumer_1
    t1 = threading.Thread(target=consumer_1.run, daemon=True)
    t1.start()
    t1.join(timeout=20.0)
    assert not t1.is_alive(), "consumer 1 did not exit"
    assert captured_1 == expected[:2], (
        f"consumer 1 expected to process exactly the first two messages, "
        f"got {len(captured_1)}: payloads do not match produced order"
    )

    # Run 2: restart with the SAME group.id and topic. The broker must hand
    # us only the unconsumed tail. Stop on the third message.
    captured_2 = []
    consumer_2_holder = {}

    def handler_2(env, payload):
        captured_2.append(bytes(payload))
        if len(captured_2) >= 1:
            consumer_2_holder["consumer"].stop()

    consumer_2 = Consumer(
        make_consumer_config(unique_topic, unique_group_id),
        handler=handler_2,
    )
    consumer_2_holder["consumer"] = consumer_2
    t2 = threading.Thread(target=consumer_2.run, daemon=True)
    t2.start()
    # Give the consumer up to 20s; if no message arrives the broker is replaying
    # from the wrong offset (or nothing at all) and we want a clear failure.
    deadline = time.time() + 20.0
    while time.time() < deadline and t2.is_alive():
        time.sleep(0.1)
    consumer_2.stop()
    t2.join(timeout=10.0)

    # Run 2 must see exactly the tail (the third message) and nothing
    # from run 1. Anything else means the committed offset was not honoured.
    assert captured_2 == [expected[2]], (
        f"consumer 2 expected to resume at the third message only; "
        f"got {len(captured_2)} message(s). Either commits did not persist "
        f"(replay of run 1) or no message was delivered (wrong offset)."
    )
