# AT4-2270: specification-only Gherkin. No step definitions yet; these
# features will be bound to pytest-bdd and wired into CI as follow-up work.
# Contract: docs/AT4-2179_message_contract.md
#
# Tags: @unit offline, @integration needs a broker, @unimplemented correct
# against the contract but not yet satisfied by the code (see the # gap: note).

@at4-2179
Feature: Candidate message envelope
  Each Kafka message value is a 4-byte envelope length, then a
  MessagePack-serialised envelope map, then the binary payload. The consumer
  splits and validates that framing before any handler sees the candidate.

  Enforces AT4-2179 section 2 (message envelope), section 5 (partitioning
  and keying), section 6 (delivery semantics) and the inline payload_mode
  framing.

  Background:
    Given a candidate adapted from row 0 of "cheetah_demo.spccl"

  @unit
  Scenario: A published candidate carries a conformant envelope
    When the candidate is serialised for publication
    Then the value begins with a 4-byte envelope length
    And the envelope decodes as a MessagePack map
    And the recovered "schema_version" is 1
    And the recovered "candidate_type" is "single_pulse"
    And the recovered "payload_mode" is "inline"
    And the recovered "message_id" is a UUID4 string
    And the recovered "producer_id" is a non-empty string
    And the recovered "timestamp_utc" is a Unix epoch milliseconds value
    And the recovered "payload_size_bytes" equals the actual payload length
    And the recovered "checksum_sha256" is the SHA-256 hex digest of the payload

  @unit
  Scenario: The consumer reconstructs the payload byte-for-byte
    When the candidate is serialised for publication
    And the consumer parses the message value
    Then the recovered payload is byte-for-byte identical to the source filterbank
    And validation of the envelope succeeds

  @unit
  Scenario: An inline payload follows the envelope with no separator
    When the candidate is serialised for publication
    Then the value length is 4 plus the envelope length plus the payload length

  @unit
  Scenario Outline: Integer envelope fields are unsigned and within contract range
    # Contract section 2 types these uint8, uint64 and uint32. msgpack packs
    # an integer at the narrowest width that fits, so schema_version 1
    # arrives as a positive fixint (0x01) rather than behind a uint8 marker:
    # the testable claim is the integer family and the contract range, not
    # the marker byte. Without this, a producer packing payload_size_bytes as
    # a signed 64-bit value would satisfy every other scenario here.
    When the candidate is serialised for publication
    Then the msgpack encoding of "<field>" is an unsigned integer
    And the recovered "<field>" is within <range>

    Examples: contract section 2 integer widths
      | field              | range  |
      | schema_version     | uint8  |
      | timestamp_utc      | uint64 |
      | payload_size_bytes | uint32 |

  @unit
  Scenario Outline: The consumer rejects a non-conformant envelope
    When the candidate is serialised with <mutation>
    Then the consumer rejects it with ContractViolationError

    Examples: envelope field violations, contract section 2
      | mutation                                      |
      | schema_version 2                              |
      | schema_version packed as a float              |
      | candidate_type "periodicity"                  |
      | payload_mode "bogus"                          |
      | message_id absent                             |
      | checksum_sha256 absent                        |
      | checksum_sha256 not matching the payload      |
      | payload_size_bytes as a string                |
      | payload_size_bytes off by one                 |
      | payload_size_bytes beyond uint32              |
      | timestamp_utc negative                        |
      | one payload byte corrupted                    |
      | payload_mode "claim_check" and no storage_uri |

  @unit
  Scenario Outline: The consumer rejects a malformed frame
    # These fail in parse_value, before any field validation runs.
    When the candidate is serialised with <mutation>
    Then the consumer rejects it with EnvelopeDecodeError

    Examples: framing violations
      | mutation                                        |
      | the envelope length prefix removed              |
      | the envelope length prefix truncated to 3 bytes |
      | an envelope length larger than the value        |
      | an envelope that is not msgpack                 |
      | an envelope that is a msgpack array             |

  @unit @unimplemented
  Scenario: A message_id that is not a UUID4 is rejected
    # gap: contract.validate types message_id as str only, so any string
    # passes. Contract section 2 specifies string (UUID4), and section 6
    # makes message_id the deduplication key, so a malformed id is not
    # cosmetic: it breaks SDP's ability to deduplicate.
    When the candidate is serialised with message_id "not-a-uuid"
    Then the consumer rejects it with ContractViolationError

  @unit
  Scenario: A claim-check envelope names its storage location
    # Contract section 2. Inline is the expected mode for the ~2.6 MB
    # candidate; claim_check is specified for oversized payloads. The subject
    # here is deliberately the consumer, not the producer: the shipped
    # producer hardcodes payload_mode "inline" with a fixed 9-key envelope
    # and has no claim-check path, so this is stated as an envelope the
    # consumer must accept rather than one PSS can currently emit.
    Given an envelope in claim_check mode with a storage_uri and storage_backend
    And no payload bytes after the envelope, per section 2
    When the consumer parses the message value
    Then validation of the envelope succeeds
    And neither payload_size_bytes nor checksum_sha256 is checked

  @unit
  Scenario: The configured topic name follows the SDP naming convention
    # Contract section 5: topic names are assigned by the SDP Receive
    # Addresses system following the [a-z][a-z0-9\-]* convention.
    Given the shipped producer and consumer configuration
    Then every configured topic name matches "[a-z][a-z0-9\-]*" in full

  @unit
  Scenario: The configured consumer group matches the contract
    # Contract section 6 names cg-pss, marked as a placeholder pending SDP
    # confirmation. Asserted so a silent drift from the contract is caught.
    Given the shipped consumer configuration
    Then the configured group id is "cg-pss"

  @unimplemented
  Scenario: A redelivered candidate is surfaced once
    # gap: delivery is at-least-once (contract section 6) with message_id as
    # the deduplication key, but the consumer holds no dedup state at all,
    # so a redelivered message reaches the handler twice. 
    When the same message_id is delivered again
    Then the handler is invoked only once

  @integration
  Scenario: The C++ producer and Python consumer agree on the wire format
    Given a Kafka broker on KAFKA_BOOTSTRAP_SERVERS
    And a unique topic with 1 partition
    And the producer is configured for scheduling block "sbi-at4-2270" and beam "beam-000"
    When the producer publishes the adapted candidate with acks=all
    And the consumer subscribes from the earliest offset
    Then the consumer receives one message within 30 seconds
    And validation of the envelope succeeds
    And the recovered "message_id" matches the message_id the producer reported
    And the recovered payload is byte-for-byte identical to the source filterbank
    And the recovered "spccl.mjd" is 56000.0000602978 to within 1e-11 days

  @integration
  Scenario: Candidates from one beam are keyed onto a single partition
    # Contract section 5: the key preserves intra-beam ordering.
    Given a Kafka broker on KAFKA_BOOTSTRAP_SERVERS
    And a unique topic with 1 partition
    And the producer is configured for scheduling block "sbi-at4-2270" and beam "beam-000"
    When the producer publishes 3 adapted candidates
    Then every message key is "sbi-at4-2270:beam-000"
    And all 3 messages are read from the same partition
    And the messages are read in the order they were published
