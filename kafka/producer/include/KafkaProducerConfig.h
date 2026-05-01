#pragma once
#include <cstdint>
#include <string>

class KafkaProducerConfig {
public:
    std::string bootstrap_servers = "localhost:9092";
    std::string topic              = "pss-single-pulse-candidates";
    std::string producer_id        = "pss-test-node-01";
    std::string acks               = "all";
    int         retries            = 5;
    int         linger_ms          = 5;
    std::string compression_type   = "none";
    std::uint32_t message_max_bytes = 4194304;

    std::uint32_t synthetic_payload_bytes        = 2300000;
    std::string   synthetic_scheduling_block_id  = "sbi-test-0001";
    std::string   synthetic_beam_id              = "beam-000";

    static KafkaProducerConfig load(const std::string& path);
};
