# AT4-2194 end-to-end validation

Demonstrates a single candidate flowing from the AT4-2180 C++ producer,
through the local Kafka broker, into the AT4-2181 Python consumer, with
the AT4-2179 envelope validated and dispatched to a handler. Happy path
only; assumes the broker is reachable and the consumer is running.

## Reproduce

From the repo root:

```
docker compose -f kafka/infra/docker-compose.yaml up -d
~/miniconda3/envs/pss-kafka/bin/pip install -e kafka/consumer
cmake -S kafka -B kafka/build && cmake --build kafka/build -j
kafka/tools/e2e_smoke.sh
```

The script writes a temporary producer and consumer config that share a
unique topic and group id, starts the consumer in the background, runs
`kafka_producer_cli --count 1`, waits for the consumer to log reception
of the same `message_id`, and prints wall-clock timings.

## Run on 2026-05-08

Bootstrap server `localhost:9092`, broker brought up fresh from
`kafka/infra/docker-compose.yaml`. Topic and group were per-run unique
(`pss-e2e-1778232982-1583`, `cg-e2e-1778232982-1583`).

Producer output:

```
  # | key                              | payload | envelope | total   | message_id
----+----------------------------------+---------+----------+---------+--------------------------------------
  1 | sbi-e2e-1778232982-1583:beam-000 | 2.19 MB |    374 B | 2.19 MB | da790378-6583-4bcf-a59c-519a1b38cf2d
```

Consumer output (relevant lines):

```
DEBUG pss_sdp_consumer.handlers received message_id=da790378-6583-4bcf-a59c-519a1b38cf2d payload_bytes=2300000
INFO  pss_sdp_consumer.metrics throughput summary processed=1 poison=0 bytes=2300378 uptime=12s
```

Same `message_id` on both sides, payload size 2,300,000 bytes matches
the producer config (`synthetic.payload_bytes`), and the consumer's
throughput summary records 2,300,378 bytes including the 374-byte
envelope and 4-byte length prefix. Envelope validation against the
AT4-2179 contract is implicit: the consumer's contract module rejects
non-conforming messages before invoking the handler, so the DEBUG line
above only fires on a valid envelope.

## Baseline metrics

| Quantity            | Value     |
|---------------------|-----------|
| Producer wall time  | 2,072 ms  |
| Producer-to-consumer wall | 3,050 ms |
| Total wall time     | 5,123 ms  |
| Payload size        | 2,300,000 B (2.19 MB) |
| Envelope size       | 374 B     |
| Throughput (1 msg)  | 0.8 msg/s, 2.19 MB over 12 s |

These are wall-clock figures from a single message and a cold start;
they bound the round trip but are not tight. Two effects dominate them:

1. The producer's 2 s wall is mostly broker discovery and the `acks=all`
   flush on the first connection, not steady-state publish cost.
2. The 3 s producer-to-consumer interval is inflated by the consumer's
   topic-not-yet-created back-off: with `KAFKA_AUTO_CREATE_TOPICS_ENABLE`
   the topic only materialises when the producer first publishes, so the
   consumer logs `UNKNOWN_TOPIC_OR_PART` warnings for several seconds
   before its metadata refresh picks up the new topic. On a topic that
   already exists, delivery is sub-second.

For meaningful throughput numbers a multi-message run on a pre-created
topic is the right next step; that is out of scope for AT4-2194 (which
specifies happy path, single message) but is recorded here so the
numbers above are not misread as steady-state.

## Outcome

- C++ producer ships a contract-conformant message: yes.
- Broker accepts and acknowledges (`acks=all` returned, exit code 0): yes.
- Python consumer receives, deserialises, validates against AT4-2179, and
  dispatches to the handler: yes.
- Round-trip wall time and payload throughput recorded: yes (above).

AT4-2194 acceptance criteria met.
