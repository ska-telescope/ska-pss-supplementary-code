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

Flags: `--config <path>`, `--count N`, `--dry-run`.
Exit codes: 0 ok, 1 config error, 2 broker error, 3 flush timeout.
