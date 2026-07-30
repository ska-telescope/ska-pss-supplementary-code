# AT4-2270: specification-only Gherkin. No step definitions yet; these
# features will be bound to pytest-bdd and wired into CI as follow-up work.
# Contract: docs/AT4-2179_message_contract.md
#
# Tags: @unit offline, @integration needs a broker, @unimplemented correct
# against the contract but not yet satisfied by the code (see the # gap: note).

@at4-2179 @unit
Feature: Cheetah candidate ingest
  A single-pulse candidate detected by Cheetah is written as one row of a
  .spccl candidate list plus a per-candidate filterbank. The adaptor
  (kafka/tools/make_cheetah_fixture.py) turns that pair into the payload.bin
  and meta.msgpack inputs the producer reads.

  Enforces AT4-2179 section 3 (SPCCL metadata) at the ingest boundary. The
  internal structure of the filterbank is out of scope: the payload is
  opaque bytes to the adaptor and to this feature.

  Background:
    Given a Cheetah candidate list "cheetah_demo.spccl" with 3 candidate rows
    And a per-candidate filterbank of 2300000 bytes

  Scenario: The filterbank becomes the payload unchanged
    When the adaptor is run for row 0
    Then the written payload is byte-for-byte identical to the source filterbank
    And the written payload is 2300000 bytes

  Scenario Outline: Any candidate row adapts to the producer's SPCCL fields
    # mjd is asserted exactly: the adaptor keeps it float64, which round-trips
    # 56000.0000602978 bit-for-bit. The other three are deliberately narrowed
    # to float32 by _F32_KEYS, so 298.8 arrives as 298.79998779296875 and
    # exact equality would fail. Tolerance here is the correct assertion, not
    # a concession.
    When the adaptor is run for row <row>
    Then the meta field "mjd" is exactly <mjd>
    And the meta field "dm" is <dm> to within float32 precision
    And the meta field "width" is <width> to within float32 precision
    And the meta field "snr" is <snr> to within float32 precision

    Examples: rows of cheetah_demo.spccl
      | row | mjd              | dm    | width | snr   |
      | 0   | 56000.0000602978 | 298.8 | 1024  | 13.22 |
      | 1   | 56000.0000617659 | 368.8 | 1024  | 15.75 |
      | 2   | 56000.0001523378 | 653.6 | 512   | 11.58 |

  Scenario: Cheetah's sigma column is carried as snr
    # Terminology difference only, same quantity. Contract section 3.
    When the adaptor is run for row 0
    Then the meta map has no "sigma" key
    And the meta field "snr" is 13.22 to within float32 precision

  Scenario: Pulse width stays in milliseconds
    # Documents intent, and deliberately asserts no unit: msgpack carries a
    # bare number, so "milliseconds" is unassertable from the encoding. The
    # testable claim is that the value passes through unconverted, which is
    # why it equals the .spccl column rather than a seconds-scaled value.
    When the adaptor is run for row 0
    Then the meta field "width" is 1024 to within float32 precision

  Scenario: Routing fields absent from .spccl fall through to producer config
    # scheduling_block_id and beam_id are not Cheetah outputs. They are
    # deliberately omitted so the producer's synthetic config defaults apply.
    When the adaptor is run for row 0
    Then the meta map has no "scheduling_block_id" key
    And the meta map has no "beam_id" key

  Scenario: A candidate list Cheetah did not write is rejected
    # Works on a copy: the committed fixture must not be mutated in place.
    Given a copy of the candidate list whose header is "not the expected header"
    When the adaptor is run for row 0
    Then adaptation fails with ValueError matching "unexpected .spccl header"

  Scenario: A candidate row that is not present is rejected
    When the adaptor is run for row 9
    Then adaptation fails with IndexError naming the number of available rows

  @unimplemented
  Scenario: The cluster label reaches the producer
    # gap: parse_spccl_row reads columns 0 to 3 only and never reads the
    # label column, so label never reaches meta.msgpack or the envelope.
    # Contract section 3 requires it as an SPCCL field.
    #
    # note: the contract types label int16, but real Cheetah cluster ids in
    # this fixture are 48611, 54056 and 129371, all outside the int16 range
    # of -32768..32767. The width in contract section 3 needs settling on
    # AT4-2179 before this is implemented; specified here as an unsigned
    # integer, which is what msgpack emits for a positive cluster id.
    When the adaptor is run for row 0
    Then the meta field "label" is exactly 48611
