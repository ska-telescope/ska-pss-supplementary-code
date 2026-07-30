# AT4-2270: specification-only Gherkin. No step definitions yet; these
# features will be bound to pytest-bdd and wired into CI as follow-up work.
# Contract: docs/AT4-2179_message_contract.md
#
# Tags: @unit offline, @integration needs a broker, @unimplemented correct
# against the contract but not yet satisfied by the code (see the # gap: note).

@at4-2179
Feature: Candidate message envelope
  Each Kafka message value is a 4-byte big-endian envelope length, then a
  MessagePack-serialised envelope map, then the binary payload. The consumer
  splits and validates that framing before any handler sees the candidate.

  Enforces AT4-2179 section 2 (message envelope), section 5 (partitioning
  and keying) and the inline payload_mode framing.

  Background:
    Given a candidate adapted from row 0 of "cheetah_demo.spccl"

  @unit
  Scenario: A published candidate carries a conformant envelope
    When the candidate is serialised for publication
    Then the value begins with a 4-byte big-endian envelope length
    And the envelope decodes as a MessagePack map
    And the envelope declares schema_version 1
    And the envelope declares candidate_type "single_pulse"
    And the envelope declares payload_mode "inline"
    And "message_id" is a UUID4 string
    And "producer_id" is a non-empty string
    And "timestamp_utc" is a Unix epoch milliseconds value within a uint64
    And "payload_size_bytes" equals the actual payload length
    And "checksum_sha256" is the SHA-256 hex digest of the payload bytes

  @unit
  Scenario: The consumer reconstructs the payload byte-for-byte
    When the candidate is serialised for publication
    And the consumer parses the message value
    Then the recovered payload is identical to the source filterbank bytes
    And validation of the envelope succeeds

  @unit
  Scenario: An inline payload follows the envelope with no separator
    When the candidate is serialised for publication
    Then the value length is 4 plus the envelope length plus the payload length

  @unit
  Scenario Outline: The consumer rejects a non-conformant message
    When the candidate is serialised with <mutation>
    Then the consumer rejects it with <error>

    Examples: envelope field violations, contract section 2
      | mutation                              | error                  |
      | schema_version 2                      | ContractViolationError |
      | candidate_type "periodicity"          | ContractViolationError |
      | payload_mode "bogus"                  | ContractViolationError |
      | message_id absent                     | ContractViolationError |
      | checksum_sha256 absent                | ContractViolationError |
      | payload_size_bytes as a string        | ContractViolationError |
      | payload_size_bytes off by one         | ContractViolationError |
      | payload_size_bytes beyond uint32      | ContractViolationError |
      | schema_version packed as a float      | ContractViolationError |
      | timestamp_utc negative                | ContractViolationError |
      | one payload byte corrupted            | ContractViolationError |
      | payload_mode "claim_check" and no storage_uri | ContractViolationError |

    Examples: framing violations, decoded before field validation
      | mutation                              | error                |
      | the envelope length prefix removed    | EnvelopeDecodeError  |
      | the envelope length prefix truncated to 3 bytes | EnvelopeDecodeError |
      | an envelope length larger than the value | EnvelopeDecodeError |
      | an envelope that is not msgpack       | EnvelopeDecodeError  |
      | an envelope that is a msgpack array    | EnvelopeDecodeError  |

  @unit
  Scenario Outline: Integer envelope fields are unsigned and within contract range
    # Contract section 2 types these uint8, uint64 and uint32. msgpack packs
    # an integer at the narrowest width that fits, so schema_version 1
    # arrives as a positive fixint rather than behind a uint8 marker: the
    # testable claim is the integer family and the contract range, not the
    # marker byte. Without this, a producer packing payload_size_bytes as a
    # signed 64-bit value would satisfy every other scenario here.
    When the candidate is serialised for publication
    Then the msgpack encoding of "<field>" is an unsigned integer
    And "<field>" is within <range>

    Examples: contract section 2 integer widths
      | field              | range  |
      | schema_version     | uint8  |
      | timestamp_utc      | uint64 |
      | payload_size_bytes | uint32 |

  @unit
  Scenario: The configured topic name follows the SDP naming convention
    # Contract section 5: topic names are assigned by the SDP Receive
    # Addresses system following the [a-z][a-z0-9\-]* convention.
    Given the shipped producer and consumer configuration
    Then every configured topic name matches "[a-z][a-z0-9\-]*"

  @unit
  Scenario: A claim-check candidate names its storage location
    # Contract section 2. Inline is the expected mode for the ~2.6 MB
    # candidate; claim_check is specified for oversized payloads.
    When the candidate is serialised in claim_check mode
    Then "storage_uri" is a non-empty string
    And "storage_backend" is a non-empty string
    And validation of the envelope succeeds

  @integration
  Scenario: The C++ producer and Python consumer agree on the wire format
    Given a Kafka broker on KAFKA_BOOTSTRAP_SERVERS
    And a unique topic with 1 partition
    And the producer is configured for scheduling block "sbi-at4-2270" and beam "beam-000"
    When the producer publishes the adapted candidate with acks=all
    And the consumer subscribes from the earliest offset
    Then the consumer receives one message within 30 seconds
    And the received envelope passes AT4-2179 validation
    And the received "message_id" matches the message_id the producer reported
    And the received payload is identical to the source filterbank bytes
    And the received "spccl.mjd" is 56000.0000602978 to within 1e-11 days

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
