#pragma once
#include <cstdint>
#include <string>
#include <vector>

struct SpcclFields {
    std::string scheduling_block_id;
    std::string beam_id;
    double mjd   = 0.0;
    float  dm    = 0.0f;
    float  width = 0.0f;
    float  snr   = 0.0f;
};

struct EncodedMessage {
    std::string key;
    std::vector<std::uint8_t> value;
    std::string message_id;
    std::uint64_t timestamp_utc_ms = 0;
};

class SpccCandidateMessage {
public:
    std::string producer_id;
    SpcclFields spccl;
    std::vector<std::uint8_t> payload;

    EncodedMessage encode() const;
};
