from __future__ import annotations
import argparse
import logging
import signal
import sys

from .config import ConsumerConfig, ConfigError
from .consumer import Consumer, resolve_handler


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="pss-sdp-consumer")
    p.add_argument("--config", default="./consumer.conf")
    p.add_argument("--group-id")
    p.add_argument("--topic")
    p.add_argument("--handler")
    p.add_argument("--log-level", default="INFO")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    log = logging.getLogger("pss_sdp_consumer.cli")

    try:
        cfg = ConsumerConfig.load(args.config)
    except (ConfigError, FileNotFoundError) as e:
        log.error("config error: %s", e)
        return 1

    if args.group_id:
        cfg.client_conf["group.id"] = args.group_id
    if args.topic:
        cfg.topic = args.topic
    if args.handler:
        cfg.handler = args.handler

    try:
        handler = resolve_handler(cfg.handler)
    except (ImportError, AttributeError, ValueError) as e:
        log.error("handler resolution failed (%s): %s", cfg.handler, e)
        return 1

    consumer = Consumer(cfg, handler=handler)

    def _stop(signum, frame):
        log.info("received signal %s; stopping", signum)
        consumer.stop()

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    try:
        consumer.run()
    except Exception as e:
        log.exception("handler raised an unhandled exception: %s", e)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
