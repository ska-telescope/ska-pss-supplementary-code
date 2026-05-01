#pragma once
#include <cstdint>
#include <string>
#include <vector>

std::vector<std::uint8_t> load_payload_bytes(const std::string& path);

struct SpcclOverrides {
    bool has_scheduling_block_id = false; std::string scheduling_block_id;
    bool has_beam_id             = false; std::string beam_id;
    bool has_mjd                 = false; double mjd   = 0.0;
    bool has_dm                  = false; float  dm    = 0.0f;
    bool has_width               = false; float  width = 0.0f;
    bool has_snr                 = false; float  snr   = 0.0f;
};

SpcclOverrides load_spccl_meta(const std::string& path);

struct CliOverrides {
    bool has_payload = false;
    std::vector<std::uint8_t> payload;
    SpcclOverrides meta;
};

CliOverrides load_overrides(const std::string& payload_path,
                            const std::string& meta_path);
