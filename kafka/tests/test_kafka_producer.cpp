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

TEST(KafkaProducerConfigTest, AcceptsInlineCommentAfterValue) {
    auto path = write_temp_config(
        "topic = real-topic # this is a trailing comment\n"
        "bootstrap.servers = localhost:9092\n"
        "producer_id = p\n"
    );
    KafkaProducerConfig cfg = KafkaProducerConfig::load(path);
    EXPECT_EQ(cfg.topic, "real-topic");
}

TEST(KafkaProducerConfigTest, AcceptsEmptyStringValue) {
    auto path = write_temp_config("topic =\nbootstrap.servers = localhost:9092\n");
    KafkaProducerConfig cfg = KafkaProducerConfig::load(path);
    EXPECT_EQ(cfg.topic, "");
}

TEST(KafkaProducerConfigTest, IgnoresBlankLines) {
    auto path = write_temp_config("\n\ntopic = t\n\n   \nbootstrap.servers = b:1\n");
    KafkaProducerConfig cfg = KafkaProducerConfig::load(path);
    EXPECT_EQ(cfg.topic, "t");
    EXPECT_EQ(cfg.bootstrap_servers, "b:1");
}

TEST(KafkaProducerConfigTest, ToleratesCrlfLineEndings) {
    auto path = write_temp_config(
        "topic = crlf-topic\r\nbootstrap.servers = host:9092\r\n");
    KafkaProducerConfig cfg = KafkaProducerConfig::load(path);
    EXPECT_EQ(cfg.topic, "crlf-topic");
    EXPECT_EQ(cfg.bootstrap_servers, "host:9092");
}

TEST(KafkaProducerConfigTest, ThrowsOnMalformedInteger) {
    auto path = write_temp_config(
        "bootstrap.servers = b:1\ntopic = t\nproducer_id = p\nretries = banana\n");
    EXPECT_THROW(KafkaProducerConfig::load(path), std::runtime_error);
}
