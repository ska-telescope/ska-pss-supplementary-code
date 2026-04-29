import logging
import pytest
from pss_sdp_consumer.handlers import log_handler

pytestmark = pytest.mark.unit


def test_log_handler_emits_debug_with_message_id(caplog):
    env = {"message_id": "abc-123"}
    payload = b"x" * 16
    with caplog.at_level(logging.DEBUG, logger="pss_sdp_consumer.handlers"):
        log_handler(env, payload)
    assert any("abc-123" in r.getMessage() for r in caplog.records)
