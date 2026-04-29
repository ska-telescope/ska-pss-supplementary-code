import logging
import pytest
from pss_sdp_consumer.metrics import ThroughputLogger

pytestmark = pytest.mark.unit


def test_records_processed_and_poison_counts():
    m = ThroughputLogger(interval_s=1.0, clock=lambda: 0.0)
    m.record_processed(100)
    m.record_processed(200)
    m.record_poison(50)
    assert m.processed_count == 2
    assert m.processed_bytes == 300
    assert m.poison_count == 1
    assert m.poison_bytes == 50


def test_maybe_log_emits_only_when_interval_elapses(caplog):
    t = [0.0]
    m = ThroughputLogger(interval_s=10.0, clock=lambda: t[0])
    m.record_processed(1000)
    with caplog.at_level(logging.INFO, logger="pss_sdp_consumer.metrics"):
        t[0] = 5.0
        m.maybe_log()
        assert not any("throughput" in r.getMessage() for r in caplog.records)
        t[0] = 10.5
        m.maybe_log()
        assert any("throughput" in r.getMessage() for r in caplog.records)


def test_interval_zero_disables_periodic_logging(caplog):
    t = [0.0]
    m = ThroughputLogger(interval_s=0, clock=lambda: t[0])
    m.record_processed(1)
    with caplog.at_level(logging.INFO, logger="pss_sdp_consumer.metrics"):
        t[0] = 1_000_000.0
        m.maybe_log()
    assert not any("throughput" in r.getMessage() for r in caplog.records)


def test_summary_logs_cumulative(caplog):
    m = ThroughputLogger(interval_s=10.0, clock=lambda: 5.0)
    m.record_processed(42)
    with caplog.at_level(logging.INFO, logger="pss_sdp_consumer.metrics"):
        m.summary()
    msgs = " ".join(r.getMessage() for r in caplog.records)
    assert "summary" in msgs
    assert "processed=1" in msgs
