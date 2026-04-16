#include <gtest/gtest.h>
#include "KafkaProducerConfig.h"
#include <fstream>

namespace {
std::string write_temp_config(const std::string& body) {
    std::string path = "/tmp/kpc_" + std::to_string(::getpid()) + ".conf";
    std::ofstream(path) << body;
    return path;
}
}

TEST(KafkaProducerConfigTest, ParsesAllRequiredFields) {
    auto path = write_temp_config(
        "# comment line\n"
        "bootstrap.servers = broker.example:9092\n"
        "topic             = my-topic\n"
        "producer_id       = node-99\n"
        "acks              = all\n"
        "retries           = 7\n"
        "linger.ms         = 12\n"
        "compression.type  = none\n"
        "message.max.bytes = 4194304\n"
        "synthetic.payload_bytes        = 2300000\n"
        "synthetic.scheduling_block_id  = sbi-x\n"
        "synthetic.beam_id              = beam-1\n"
    );
    KafkaProducerConfig cfg = KafkaProducerConfig::load(path);
    EXPECT_EQ(cfg.bootstrap_servers, "broker.example:9092");
    EXPECT_EQ(cfg.topic, "my-topic");
    EXPECT_EQ(cfg.producer_id, "node-99");
    EXPECT_EQ(cfg.acks, "all");
    EXPECT_EQ(cfg.retries, 7);
    EXPECT_EQ(cfg.linger_ms, 12);
    EXPECT_EQ(cfg.compression_type, "none");
    EXPECT_EQ(cfg.message_max_bytes, 4194304u);
    EXPECT_EQ(cfg.synthetic_payload_bytes, 2300000u);
    EXPECT_EQ(cfg.synthetic_scheduling_block_id, "sbi-x");
    EXPECT_EQ(cfg.synthetic_beam_id, "beam-1");
}

TEST(KafkaProducerConfigTest, ThrowsOnMissingFile) {
    EXPECT_THROW(KafkaProducerConfig::load("/no/such/file.conf"),
                 std::runtime_error);
}

TEST(KafkaProducerConfigTest, IgnoresUnknownKeysAndComments) {
    auto path = write_temp_config(
        "# header\n"
        "bootstrap.servers=localhost:9092\n"
        "topic=t\n"
        "producer_id=p\n"
        "unknown.key=ignored\n"
    );
    KafkaProducerConfig cfg = KafkaProducerConfig::load(path);
    EXPECT_EQ(cfg.bootstrap_servers, "localhost:9092");
}
