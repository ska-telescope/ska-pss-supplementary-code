# kafka/consumer/pss_sdp_consumer/consumer.py
from __future__ import annotations
import importlib
import logging
import threading

from confluent_kafka import Consumer as KafkaConsumer, KafkaError

from .config import ConsumerConfig
from .contract import EnvelopeDecodeError, ContractViolationError, parse_value, validate
from .handlers import Handler
from .metrics import ThroughputLogger

_log = logging.getLogger(__name__)


class HandlerError(Exception):
    """Raised when the user-supplied handler raises an exception.

    The original exception is attached as ``__cause__`` so the CLI can
    distinguish handler failures (exit 3) from consumer/client failures
    (exit 2) without losing the underlying traceback.
    """


def resolve_handler(spec: str) -> Handler:
    if ":" not in spec:
        raise ValueError(f"handler spec {spec!r} must be 'module:callable'")
    mod_name, _, attr = spec.partition(":")
    mod = importlib.import_module(mod_name)
    return getattr(mod, attr)


class Consumer:
    def __init__(self, config: ConsumerConfig, handler: Handler | None = None):
        self._config = config
        self._handler = handler if handler is not None else resolve_handler(config.handler)
        client_conf = dict(config.client_conf)
        # Force at-least-once semantics regardless of config file content.
        client_conf["enable.auto.commit"] = "false"
        self._client = KafkaConsumer(client_conf)
        self._metrics = ThroughputLogger(interval_s=config.metrics_interval_s)
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        self._client.subscribe([self._config.topic])
        try:
            while not self._stop.is_set():
                msg = self._client.poll(timeout=1.0)
                self._metrics.maybe_log()
                if msg is None:
                    continue
                if msg.error():
                    # PARTITION_EOF is an informational event ("we have caught up"),
                    # not an error; librdkafka only surfaces it when explicitly
                    # enabled but we still guard against it here so an enabled
                    # client doesn't spam the log on every quiet poll.
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    _log.warning("client error: %s", msg.error())
                    # Batch commits are a future optimisation; manual sync per-message
                    # commit is the simplest correct at-least-once shape for now.
                    continue
                try:
                    envelope, payload = parse_value(msg.value())
                    validate(envelope, payload)
                except (EnvelopeDecodeError, ContractViolationError) as e:
                    _log.error(
                        "poison message topic=%s partition=%s offset=%s reason=%s",
                        msg.topic(), msg.partition(), msg.offset(), e,
                    )
                    self._client.commit(message=msg, asynchronous=False)
                    self._metrics.record_poison(len(msg.value()))
                    continue
                # Handler exceptions propagate by design: a buggy handler should
                # crash loudly rather than silently advance the offset. Wrap them
                # in HandlerError so the CLI can distinguish handler failures
                # from consumer/client failures via different exit codes.
                try:
                    self._handler(envelope, payload)
                except Exception as e:
                    raise HandlerError(
                        f"handler {self._config.handler} raised {type(e).__name__}: {e}"
                    ) from e
                self._client.commit(message=msg, asynchronous=False)
                self._metrics.record_processed(len(msg.value()))
        finally:
            self._metrics.summary()
            self._client.close()
