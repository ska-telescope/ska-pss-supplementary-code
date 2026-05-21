#!/usr/bin/env bash
# AT4-2194: end-to-end smoke. C++ producer ships one candidate; Python
# consumer receives, validates against the AT4-2179 envelope, dispatches.
# Assumes the broker (kafka/infra/docker-compose.yaml) is already up and
# the consumer package is installed in the pss-kafka conda env. Uses a
# unique topic and group id so the run is isolated from prior state.
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
producer_bin="${repo_root}/build/producer/kafka_producer_cli"
consumer_bin="${HOME}/miniconda3/envs/pss-kafka/bin/pss-sdp-consumer"
bootstrap="${KAFKA_BOOTSTRAP_SERVERS:-localhost:9092}"

run_id="$(date +%s)-$$"
topic="pss-e2e-${run_id}"
group="cg-e2e-${run_id}"
work="$(mktemp -d -t at4-2194-XXXXXX)"
trap 'rm -rf "${work}"' EXIT

producer_conf="${work}/producer.conf"
consumer_conf="${work}/consumer.conf"
consumer_log="${work}/consumer.log"
producer_log="${work}/producer.log"

cat > "${producer_conf}" <<EOF
bootstrap.servers = ${bootstrap}
topic             = ${topic}
producer_id       = pss-e2e-${run_id}
acks              = all
retries           = 5
linger.ms         = 5
compression.type  = none
message.max.bytes = 4194304
synthetic.payload_bytes        = 2300000
synthetic.scheduling_block_id  = sbi-e2e-${run_id}
synthetic.beam_id              = beam-000
EOF

cat > "${consumer_conf}" <<EOF
bootstrap.servers   = ${bootstrap}
topic               = ${topic}
group.id            = ${group}
enable.auto.commit  = false
auto.offset.reset   = earliest
session.timeout.ms  = 10000
max.poll.interval.ms = 300000
fetch.max.bytes     = 4194304
message.max.bytes   = 4194304
handler             = pss_sdp_consumer.handlers:log_handler
metrics.interval_s  = 1
EOF

echo "[e2e] topic=${topic} group=${group}"
echo "[e2e] starting consumer in background"
"${consumer_bin}" --config "${consumer_conf}" --log-level DEBUG \
    >"${consumer_log}" 2>&1 &
consumer_pid=$!
trap 'kill ${consumer_pid} 2>/dev/null || true; wait ${consumer_pid} 2>/dev/null || true; rm -rf "${work}"' EXIT

# Best-effort wait for the consumer to join the group before we publish, so
# the delivery-wall timing reflects a warm consumer rather than group-join
# overhead. Correctness does not depend on this: auto.offset.reset=earliest
# ensures the message is picked up whenever the consumer joins, and the
# "received message_id=" check below is the real PASS/FAIL gate. If none of
# the readiness strings appear (e.g. the log format has drifted), we warn
# and proceed rather than fail.
ready=0
for i in $(seq 1 30); do
    if grep -q "Consumer ready" "${consumer_log}" 2>/dev/null \
       || grep -q "subscribed" "${consumer_log}" 2>/dev/null \
       || grep -q "assigned" "${consumer_log}" 2>/dev/null; then
        ready=1
        break
    fi
    sleep 0.2
done
if [[ ${ready} -eq 0 ]]; then
    echo "[e2e] warning: no readiness marker in consumer log after 6s; proceeding anyway"
fi

t_start_ns=$(date +%s%N)
echo "[e2e] producing 1 message"
"${producer_bin}" --config "${producer_conf}" --count 1 --compact \
    >"${producer_log}" 2>&1
producer_rc=$?
t_produced_ns=$(date +%s%N)

if [[ ${producer_rc} -ne 0 ]]; then
    echo "[e2e] producer failed (rc=${producer_rc})"
    cat "${producer_log}"
    exit 1
fi

# Wait for the consumer to log reception of the message.
for i in $(seq 1 100); do
    if grep -q "received message_id=" "${consumer_log}"; then
        break
    fi
    sleep 0.1
done
t_received_ns=$(date +%s%N)

# Stop the consumer cleanly so the throughput summary lands in the log.
kill -INT "${consumer_pid}" 2>/dev/null || true
wait "${consumer_pid}" 2>/dev/null || true

if ! grep -q "received message_id=" "${consumer_log}"; then
    echo "[e2e] consumer never received the message"
    echo "--- consumer log ---"
    cat "${consumer_log}"
    exit 1
fi

produce_ms=$(( (t_produced_ns - t_start_ns) / 1000000 ))
deliver_ms=$(( (t_received_ns - t_produced_ns) / 1000000 ))
total_ms=$(( (t_received_ns - t_start_ns) / 1000000 ))

msg_id=$(grep -oE "message_id=[0-9a-f-]+" "${consumer_log}" | head -1 | cut -d= -f2)
payload_bytes=$(grep -oE "payload_bytes=[0-9]+" "${consumer_log}" | head -1 | cut -d= -f2)

echo
echo "[e2e] PASS"
echo "  message_id          : ${msg_id}"
echo "  payload_bytes       : ${payload_bytes}"
echo "  producer wall (ms)  : ${produce_ms}"
echo "  delivery wall (ms)  : ${deliver_ms}"
echo "  total wall (ms)     : ${total_ms}"
echo
echo "[e2e] producer log:"
sed 's/^/  | /' "${producer_log}"
echo
echo "[e2e] consumer log (last 20 lines):"
tail -n 20 "${consumer_log}" | sed 's/^/  | /'
