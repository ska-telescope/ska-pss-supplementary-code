import pytest
from pss_sdp_consumer.config import ConsumerConfig, ConfigError

pytestmark = pytest.mark.unit


def test_loads_known_application_keys(tmp_path):
    p = tmp_path / "consumer.conf"
    p.write_text(
        "# comment\n"
        "bootstrap.servers = localhost:9092\n"
        "topic = my-topic\n"
        "group.id = my-group\n"
        "handler = pss_sdp_consumer.handlers:log_handler\n"
        "metrics.interval_s = 7\n"
    )
    cfg = ConsumerConfig.load(p)
    assert cfg.topic == "my-topic"
    assert cfg.handler == "pss_sdp_consumer.handlers:log_handler"
    assert cfg.metrics_interval_s == 7
    # Dotted librdkafka keys are passed through verbatim
    assert cfg.client_conf["bootstrap.servers"] == "localhost:9092"
    assert cfg.client_conf["group.id"] == "my-group"


def test_unknown_bare_key_rejected(tmp_path):
    p = tmp_path / "consumer.conf"
    p.write_text("nonsense = oops\n")
    with pytest.raises(ConfigError, match="nonsense"):
        ConsumerConfig.load(p)


def test_non_integer_metrics_interval_raises_with_context(tmp_path):
    p = tmp_path / "consumer.conf"
    p.write_text(
        "bootstrap.servers = localhost:9092\n"
        "topic = t\n"
        "group.id = g\n"
        "metrics.interval_s = not-a-number\n"
    )
    with pytest.raises(ConfigError) as excinfo:
        ConsumerConfig.load(p)
    msg = str(excinfo.value)
    assert "metrics.interval_s" in msg
    assert f"{p}:4" in msg


def test_dotted_unknown_keys_pass_through(tmp_path):
    p = tmp_path / "consumer.conf"
    p.write_text(
        "bootstrap.servers = localhost:9092\n"
        "topic = t\n"
        "group.id = g\n"
        "session.timeout.ms = 12345\n"
    )
    cfg = ConsumerConfig.load(p)
    assert cfg.client_conf["session.timeout.ms"] == "12345"
