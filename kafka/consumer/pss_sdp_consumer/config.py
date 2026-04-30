from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path


class ConfigError(ValueError):
    pass


@dataclass
class ConsumerConfig:
    topic: str
    handler: str
    metrics_interval_s: int
    client_conf: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path) -> "ConsumerConfig":
        path = Path(path)
        topic = handler = None
        metrics_interval_s = 10
        client_conf: dict[str, str] = {}

        for lineno, raw in enumerate(path.read_text().splitlines(), start=1):
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            if "=" not in line:
                raise ConfigError(f"{path}:{lineno}: missing '='")
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip()

            if k == "topic":
                topic = v
            elif k == "handler":
                handler = v
            elif k == "metrics.interval_s":
                try:
                    metrics_interval_s = int(v)
                except ValueError as e:
                    raise ConfigError(
                        f"{path}:{lineno}: metrics.interval_s must be an integer (got {v!r})"
                    ) from e
            elif "." in k:
                client_conf[k] = v
            else:
                raise ConfigError(f"{path}:{lineno}: unknown key {k!r}")

        if topic is None:
            raise ConfigError(f"{path}: missing required key 'topic'")
        if handler is None:
            handler = "pss_sdp_consumer.handlers:log_handler"
        if "bootstrap.servers" not in client_conf:
            raise ConfigError(f"{path}: missing required key 'bootstrap.servers'")
        if "group.id" not in client_conf:
            raise ConfigError(f"{path}: missing required key 'group.id'")

        return cls(
            topic=topic,
            handler=handler,
            metrics_interval_s=metrics_interval_s,
            client_conf=client_conf,
        )
