# PSS to SDP Kafka consumer (AT4-2181)

A Python consumer that reads single-pulse-candidate messages from the
PSS-to-SDP Kafka topic, validates each envelope against the AT4-2179
contract, and dispatches the decoded record to a pluggable handler.
Offsets are committed manually after the handler returns, so a crashing
handler will not silently lose data.

All commands below assume the working directory is the repo root.

## Purpose

This is the production-shaped consumer artefact for AT4-2181. It is the
counterpart to the AT4-2180 C++ producer and is intended to slot into the
SDP side of the integration. For a one-row-per-message viewer used during
demos and round-trip checks, see
[`kafka/tools/consume_compact.py`](../tools/consume_compact.py); that
script does not validate envelopes, does not commit offsets, and is not
the production consumer.

## Install

The package lives under `kafka/consumer/`. Install it in editable mode
into the same `pss-kafka` conda env that the rest of the kafka tooling
uses:

```
~/miniconda3/envs/pss-kafka/bin/pip install -e kafka/consumer
```

This exposes the `pss-sdp-consumer` CLI on the env's `PATH`.

## Configuration

The CLI reads a librdkafka-style properties file. A reference file lives
at `kafka/consumer/config/consumer.conf`. Keys with a dot (e.g.
`bootstrap.servers`) pass through verbatim to librdkafka; bare keys are
application-level and the loader rejects unknown ones.

| Key                      | Kind        | Required | Notes                                                                                  |
|--------------------------|-------------|----------|----------------------------------------------------------------------------------------|
| `bootstrap.servers`      | librdkafka  | yes      | Broker list, e.g. `localhost:9092`.                                                    |
| `group.id`               | librdkafka  | yes      | Consumer group identifier.                                                             |
| `topic`                  | application | yes      | Topic to subscribe to.                                                                 |
| `handler`                | application | no       | `module:callable` form. Defaults to `pss_sdp_consumer.handlers:log_handler`.           |
| `metrics.interval_s`     | application | no       | Integer seconds for periodic throughput logging. `0` disables. Default `10`.           |
| `enable.auto.commit`     | librdkafka  | no       | Forced to `false` in code; leave at `false` in the config.                             |
| `auto.offset.reset`      | librdkafka  | no       | Standard librdkafka behaviour, e.g. `earliest` or `latest`.                            |
| `session.timeout.ms`     | librdkafka  | no       | Tuning knob, passed through verbatim.                                                  |
| `max.poll.interval.ms`   | librdkafka  | no       | Tuning knob, passed through verbatim.                                                  |
| `fetch.max.bytes`        | librdkafka  | no       | Tuning knob, passed through verbatim.                                                  |
| `message.max.bytes`      | librdkafka  | no       | Tuning knob, passed through verbatim.                                                  |

## CLI flags

```
pss-sdp-consumer [--config <path>] [--group-id <id>] [--topic <name>]
                 [--handler <module:callable>] [--log-level <LEVEL>]
```

- `--config <path>`: properties file. Default `./consumer.conf`.
- `--group-id <id>`: overrides `group.id` from the config.
- `--topic <name>`: overrides `topic` from the config.
- `--handler <module:callable>`: overrides `handler` from the config.
- `--log-level <LEVEL>`: stdlib logging level. Default `INFO`.

Exit codes: `0` clean shutdown, `1` config or handler-resolution error,
`3` unhandled handler exception.

## Run recipe

```
docker compose -f kafka/infra/docker-compose.yaml up -d
~/miniconda3/envs/pss-kafka/bin/pip install -e kafka/consumer
~/miniconda3/envs/pss-kafka/bin/pss-sdp-consumer \
    --config kafka/consumer/config/consumer.conf --log-level INFO
# Ctrl-C to stop. A throughput summary is logged on shutdown.
```

## Tests

Tests live under `kafka/tests/` and are split by pytest marker:

- `unit`: offline tests, no broker required.
  ```
  pytest kafka/tests -v -m unit
  ```
- `integration`: requires a reachable broker. The integration tests read
  `KAFKA_BOOTSTRAP_SERVERS` (default `localhost:9092`).
  ```
  pytest kafka/tests -v -m integration
  ```

## Horizontal scaling

The consumer is a standard librdkafka group consumer, so scaling is done
by running multiple instances with the same `group.id`. The default
broker config in this repo creates the topic with a single partition,
which caps useful parallelism at one. A check with two instances sharing
`group.id at4-2181-scale-check` against the single-partition topic
confirmed librdkafka assigned the only partition to the first instance,
and the second instance sat idle as a warm standby until the first left
the group. This matches AT4-2179 section 5: increase the partition count
to scale horizontally; until then, additional instances act as warm
standbys rather than parallel workers.

## Relationship with `tools/consume_compact.py`

`kafka/tools/consume_compact.py` is a compact viewer for demos and
round-trip checks. It prints one row per message in the same layout as
the producer's `--compact` mode, which makes diffing by `message_id`
trivial. It deliberately skips envelope validation and manual offset
management, so it is not a substitute for `pss-sdp-consumer`. Use the
viewer for eyeballing traffic; use `pss-sdp-consumer` for anything that
needs validated, at-least-once delivery to a handler.
