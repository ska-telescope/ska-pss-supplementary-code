# AT4-2270: specification-only Gherkin. No step definitions yet; these
# features will be bound to pytest-bdd and wired into CI as follow-up work.
# Contract: docs/AT4-2179_message_contract.md
#
# Tags: @unit offline, @integration needs a broker, @unimplemented correct
# against the contract but not yet satisfied by the code (see the # gap: note).

@at4-2179
Feature: SPCCL metadata in the envelope
  The SPCCL record travels as a nested MessagePack map under the envelope key
  "spccl". Field widths are pinned by AT4-2179 section 3 and the reason is
  numerical, not stylistic: MJD is around 6e4 days, so float32's seven
  significant digits resolve only to seconds and would destroy the
  millisecond and microsecond arrival-time precision the candidate exists to
  report. Every other floating-point scalar is float32 by contract; label is
  an integer cluster id.

  Float assertions here are made on the encoded msgpack type marker, not on
  the decoded Python value. Python has a single float type, so decoding and
  then type-checking would pass even where the producer had packed float32
  and silently truncated the MJD. Marker assertions are valid for floats
  precisely because msgpack does not narrow them.

  Integers are different: msgpack packs them at the narrowest width that
  fits, so label is asserted by family and range rather than by marker.

  Background:
    Given a candidate adapted from row 0 of "cheetah_demo.spccl"

  @unit
  Scenario: The envelope carries a nested SPCCL map
    When the candidate is serialised for publication
    Then the envelope key "spccl" is a MessagePack map

  @unit
  Scenario Outline: Each SPCCL field is packed at its contract width
    When the candidate is serialised for publication
    Then the msgpack type marker of "spccl.<field>" is <msgpack_type>

    Examples: contract section 3 field widths
      | field | msgpack_type |
      | mjd   | float64      |
      | dm    | float32      |
      | width | float32      |
      | snr   | float32      |

  @unit
  Scenario: MJD survives the round trip at sub-millisecond precision
    # 1e-11 days is around 1 microsecond. Packed as float32 the same value
    # lands roughly 4e-3 days (around 350 seconds) out.
    When the candidate is serialised for publication
    Then the recovered "spccl.mjd" is 56000.0000602978 to within 1e-11 days

  @unit
  Scenario Outline: The remaining scalars survive at float32 precision
    When the candidate is serialised for publication
    Then the recovered "spccl.<field>" is <value> to within float32 precision

    Examples:
      | field | value |
      | dm    | 298.8 |
      | width | 1024  |
      | snr   | 13.22 |

  @unit
  Scenario: The routing identifiers are carried alongside the SPCCL scalars
    # The producer packs these into the spccl map from its own config; they
    # are not Cheetah outputs. They are the source of the message key.
    # note: contract section 3 documents label but omits these two fields,
    # although the producer packs both. The contract table needs updating;
    # the code is already correct, so this scenario is not tagged as a gap.
    When the candidate is serialised for publication
    Then the recovered "spccl.scheduling_block_id" is a non-empty string
    And the recovered "spccl.beam_id" is a non-empty string
    And the message key is the scheduling block id and the beam id joined by a colon

  @unit @unimplemented
  Scenario: The cluster label is carried as an unsigned integer
    # gap: the adaptor never reads the label column and the producer packs no
    # label field, so the contract's label never reaches the wire.
    #
    # note: contract section 3 types label int16, but that cannot be right.
    # The real Cheetah cluster ids in this fixture are 48611, 54056 and
    # 129371, all outside int16's -32768..32767, and msgpack emits unsigned
    # markers for positive integers anyway (48611 -> cd bde3, uint16;
    # 129371 -> ce 0001f95b, uint32). An int16 marker assertion could never
    # hold alongside a real label value. Specified as family-plus-range, as
    # for the envelope integers. The declared width needs settling on
    # AT4-2179 before this is implemented.
    When the candidate is serialised for publication
    Then the msgpack encoding of "spccl.label" is an unsigned integer
    And the recovered "spccl.label" is within uint32
    And the recovered "spccl.label" is exactly 48611

  @unit @unimplemented
  Scenario: An MJD packed as float32 is rejected
    # gap: contract.validate carries TODO(AT4-2179) and performs no
    # field-level SPCCL checks, so a truncated MJD reaches the handler.
    When the candidate is serialised with "spccl.mjd" packed as float32
    Then the consumer rejects it with ContractViolationError

  @unit @unimplemented
  Scenario Outline: A missing SPCCL field is rejected
    # gap: as above, no field-level SPCCL validation exists.
    When the candidate is serialised without "spccl.<field>"
    Then the consumer rejects it with ContractViolationError

    Examples:
      | field |
      | mjd   |
      | dm    |
      | width |
      | snr   |
      | label |

  @unit
  Scenario Outline: An SPCCL record that is not a map is rejected
    When the candidate is serialised with <mutation>
    Then the consumer rejects it with ContractViolationError

    Examples:
      | mutation                |
      | "spccl" as a string     |
      | "spccl" absent entirely |
