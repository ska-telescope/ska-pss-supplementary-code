# Local Kafka broker

Single-node KRaft broker for AT4-2180 producer tests. Env vars mirror the
SDP `ska-sdp-testing` Helm chart, with `message.max.bytes` and
`replica.fetch.max.bytes` raised to 4 MB to fit ~2.3 MB candidate messages.

## Run

```
docker compose -f kafka/infra/docker-compose.yaml up -d
docker compose -f kafka/infra/docker-compose.yaml down
```

## Verify

```
docker exec pss-kafka /opt/kafka/bin/kafka-topics.sh \
    --bootstrap-server localhost:9092 --list
```
