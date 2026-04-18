# AT4-2180 standalone Kafka producer

A C++ producer that ships single-pulse-candidate messages per the
`docs/AT4-2179_message_contract.md` contract, plus a local test broker
that mirrors the SDP `ska-sdp-testing` Helm chart.

## Build

```
cmake -S kafka -B kafka/build
cmake --build kafka/build -j
```

## Test

```
docker compose -f kafka/infra/docker-compose.yaml up -d
ctest --test-dir kafka/build --output-on-failure
docker compose -f kafka/infra/docker-compose.yaml down
```

`ctest -L unit` runs only the broker-free tests.

## Run the CLI

```
kafka/build/producer/kafka_producer_cli \
    --config kafka/producer/config/producer.conf
```

Flags: `--config <path>`, `--count N`, `--dry-run`, `--compact`.
By default each shipped message is printed as a vertical block; `--compact`
switches to a one-row-per-message table.
Exit codes: 0 ok, 1 config error, 2 broker error, 3 flush timeout.

Sample default output:

```
── message 1 of 1 ──
  key               : sbi-test-0001:beam-000
  producer_id       : pss-test-node-01
  message_id        : 2b42ed61-33f5-4e65-b7c6-2bd741d70014
  timestamp_utc     : 2026-04-18T08:25:26.069Z
  scheduling_block  : sbi-test-0001
  beam_id           : beam-000
  mjd               : 60000
  dm                : 50
  width             : 0.001
  snr               : 10
  payload_bytes     : 2300000  (2.19 MB)
  envelope_bytes    : 357
  total_value_bytes : 2300361
```

Sample `--compact` output:

```
  # | key                        | payload   | envelope | total     | message_id
----+----------------------------+-----------+----------+-----------+--------------------------------------
  1 | sbi-test-0001:beam-000     |   2.19 MB |    357 B |   2.19 MB | dd560ba9-b095-4212-8a94-e789fa987d17
```

## Verify with the consumer helper

`kafka/tools/consume_compact.py` reads messages back from the broker and prints
them in the same `--compact` table layout, so producer and consumer rows can be
diff-compared by `message_id`. It needs `confluent-kafka` and `msgpack` — a
conda env keeps those out of the system Python:

```
conda create -n pss-kafka -c conda-forge -y python=3.11 python-confluent-kafka msgpack-python
conda activate pss-kafka
```

Default mode (no `--count`) tails the topic from the current end — leave it
running, then send messages from another shell and watch them appear.

```
python kafka/tools/consume_compact.py                    # tail forever (Ctrl-C to stop)
python kafka/tools/consume_compact.py --count 5          # last 5 then exit
python kafka/tools/consume_compact.py --from-beginning   # all existing, then keep tailing
```

Round-trip check:

```
kafka/build/producer/kafka_producer_cli --config kafka/producer/config/producer.conf --count 3 --compact
python kafka/tools/consume_compact.py --count 3
```

The `message_id` column should match line-for-line between the two tables.
