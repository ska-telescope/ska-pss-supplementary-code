# PSS–SDP Kafka Message Contract - Single Pulse Candidates

**Document status:** Draft
**Ticket:** AT4-2179
**Relates to:** SP-6604

---

## 1. Scope

This contract defines the Kafka message format for single pulse candidates produced by PSS and consumed by SDP. It covers the message envelope, SPCCL metadata fields, filterbank payload structure, partitioning and keying strategy, and delivery semantics.

Pulsar search (FDAS/periodicity) candidates are out of scope.

---

## 2. Message Envelope

Each Kafka message consists of a MessagePack-serialised envelope followed by a binary payload. The envelope carries versioning, identity, integrity, and payload routing fields.

| Field | Type | Description |
|---|---|---|
| `schema_version` | uint8 | Contract version. Current: `1` |
| `message_id` | string (UUID4) | Unique message identifier |
| `producer_id` | string | Producing PSS node or beam identifier |
| `timestamp_utc` | uint64 | Message production time, Unix epoch milliseconds |
| `candidate_type` | string | Fixed value: `"single_pulse"` |
| `payload_mode` | string | `"inline"` or `"claim_check"` |
| `payload_size_bytes` | uint32 | Total byte length of the binary payload section |
| `checksum_sha256` | string | SHA-256 hex digest of the binary payload |

For `payload_mode = "claim_check"`, the following additional fields are present:

| Field | Type | Description |
|---|---|---|
| `storage_uri` | string | Storage-agnostic URI to the payload object (e.g. `s3://bucket/key` or `pvc:///path/to/file`) |
| `storage_backend` | string | Backend hint: `"ceph_rgw"`, `"pvc"`, etc. |

For `payload_mode = "inline"`, the binary payload immediately follows the envelope in the Kafka message value.

---

## 3. SPCCL Metadata

The SPCCL record is serialised as part of the MessagePack envelope (nested map under key `spccl`). The specific fields and types are defined by the Cheetah SPCCL data model and are to be confirmed against the current Cheetah implementation as part of AT4-2179.

**Open:** Full enumeration of SPCCL fields, types, units, and any fields required specifically for the SDP interface (e.g. `beam_id`, `scheduling_block_id`) to be agreed with Ben Stappers / Lina and validated against BDD feature files.

---

## 4. Binary Payload - Dedispersed Filterbank Cube

The binary payload is a filterbank containing the dedispersed data cube for the candidate window.

Structure: standard sigproc header block, followed by raw time-frequency samples in row-major order (time outermost, frequency innermost).

| Property | Value | Notes |
|---|---|---|
| Format | Sigproc filterbank | As per original interface document |
| Dimensions | `n_time_samples` × `n_channels` | To be confirmed - see open questions |
| Sample type | float32 | TBC |
| Dispersion correction | Applied | Dedispersed at candidate DM before export |
| Time window | Centred on pulse arrival time | N samples either side of pulse |

The sigproc header within the payload duplicates key observational parameters for standalone file compatibility. The envelope checksum covers the entire payload including the sigproc header.

Estimated payload size: approximately 2.6 MB per candidate (SPCCL + filterbank cube combined).

---

## 5. Partitioning and Keying Strategy

**Kafka message key:** `{scheduling_block_id}:{beam_id}`

This ensures all candidates from the same beam within a scheduling block are routed to the same partition, preserving intra-beam ordering. Cross-beam ordering is not required.

**Number of partitions:** 1 (per agreed SDP cluster configuration from AT4-2189). Revisit if candidate rate requires parallelism.

**Topic name:** Assigned via the SDP Receive Addresses system at subarray-configure time, following the `[a-z][a-z0-9\-]*` convention.

---

## 6. Delivery Semantics

**At-least-once delivery.** The Cheetah producer uses `acks=all` and retries on transient broker failure. SDP consumers must handle duplicate messages. Deduplication key: `message_id`.

**Queue retention:** 1 minute. SDP must consume within this window or messages are lost. No replay beyond this TTL.

**Consumer group:** `cg-pss` (placeholder - to be confirmed with SDP).

**Offset management:** Manual commit by SDP consumer after successful processing, as per AT4-2181.

---

## 7. BDD Feature File Alignment

| Feature file | Scenario | Contract field(s) |
|---|---|---|
| `candidate_streaming.feature` | Receive single pulse candidate | `spccl.*`, payload filterbank |
| `candidate_streaming.feature` | Extract individual candidate fields | SPCCL metadata fields |
| `pss_sdp_configuration.feature` | Sigproc sink configured | Filterbank payload format |
| `pss_sdp_configuration.feature` | Receiver restart / duplicate handling | `message_id`, at-least-once semantics |

**Open:** Full pass against all BDD feature files required as part of AT4-2179 acceptance.

---

## 8. Open Questions

1. Confirm filterbank cube dimensions (`n_time_samples`, `n_channels`, `time_resolution`) - Ben Stappers / Lina.
2. Confirm SPCCL fields required in the Kafka contract and their types/units - align with current Cheetah implementation.
3. Confirm sample type (float32 assumed).
4. Confirm `payload_mode` default: will candidates always be inline at ~2.6 MB, or is claim-check required? Depends on agreed `max.message.bytes` for the topic.
5. Confirm consumer group ID with SDP (Dominic Schaff).
6. Confirm `beam_id` type and format - align with SDP Receive Addresses schema.
