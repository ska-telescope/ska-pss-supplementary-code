#!/usr/bin/env python3
"""Consume PSS single-pulse-candidate messages and render them in the same
compact table format the producer prints with --compact. Ad-hoc verification
helper for AT4-2180; not part of the producer artifact.

Wire format (per docs/AT4-2179_message_contract.md):
    [BE u32 envelope_len][msgpack envelope][raw payload bytes]

Run inside the pss-kafka conda env:
    ~/miniconda3/envs/pss-kafka/bin/python tools/consume_compact.py --count 2
"""
import argparse
import struct
import sys

import msgpack
from confluent_kafka import Consumer, TopicPartition


def parse_value(buf: bytes):
    env_len = struct.unpack(">I", buf[:4])[0]
    env = msgpack.unpackb(buf[4:4 + env_len], raw=False)
    payload_len = len(buf) - 4 - env_len
    return env, env_len, payload_len


def fmt_mb(n: int) -> str:
    return f"{n / (1024 * 1024):.2f} MB"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", default="localhost:9092")
    ap.add_argument("--topic",     default="pss-single-pulse-candidates")
    ap.add_argument("--count",     type=int, default=None,
                    help="messages to read (per partition); omit to tail forever")
    ap.add_argument("--from-beginning", action="store_true",
                    help="read from offset 0 instead of seeking near the end")
    args = ap.parse_args()

    c = Consumer({
        "bootstrap.servers":  args.bootstrap,
        "group.id":           "pss-consume-compact",
        "enable.auto.commit": False,
        "message.max.bytes":  4194304,
    })

    md = c.list_topics(args.topic, timeout=5.0)
    parts = md.topics[args.topic].partitions
    tps = []
    expected = 0
    for pid in parts:
        tp = TopicPartition(args.topic, pid)
        lo, hi = c.get_watermark_offsets(tp, timeout=5.0)
        if args.from_beginning:
            start = lo
        elif args.count is None:
            start = hi  # tail mode: only new messages
        else:
            start = max(lo, hi - args.count)
        tps.append(TopicPartition(args.topic, pid, start))
        if args.count is not None:
            expected += min(args.count, hi - start)
    c.assign(tps)

    print("  # | key                        | payload   | envelope | total     | message_id")
    print("----+----------------------------+-----------+----------+-----------+--------------------------------------")

    seen = 0
    try:
        while args.count is None or seen < expected:
            msg = c.poll(5.0)
            if msg is None:
                if args.count is not None:
                    print(f"timeout after {seen}/{expected} messages",
                          file=sys.stderr)
                    break
                continue  # tail mode: keep waiting
            if msg.error():
                print(f"consumer error: {msg.error()}", file=sys.stderr)
                continue
            env, env_len, payload_len = parse_value(msg.value())
            total = 4 + env_len + payload_len
            seen += 1
            key = msg.key().decode() if msg.key() else "<no key>"
            print(f"{seen:3d} | {key:<26} | {fmt_mb(payload_len):>9} | "
                  f"{str(env_len) + ' B':>8} | {fmt_mb(total):>9} | {env['message_id']}",
                  flush=True)
    except KeyboardInterrupt:
        print(f"\ninterrupted after {seen} messages", file=sys.stderr)

    c.close()
    if args.count is None:
        return 0
    return 0 if seen == expected else 1


if __name__ == "__main__":
    sys.exit(main())
