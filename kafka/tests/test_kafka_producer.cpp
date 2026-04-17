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
        "bootstrap.servers = b:1\ntopic = t\nproducer_id = p\nretries = not-a-number\n");
    try {
        KafkaProducerConfig::load(path);
        FAIL() << "expected std::runtime_error to be thrown";
    } catch (const std::runtime_error& e) {
        const std::string msg = e.what();
        EXPECT_NE(std::string::npos, msg.find("retries"))
            << "exception message did not mention key 'retries': " << msg;
        EXPECT_NE(std::string::npos, msg.find("not-a-number"))
            << "exception message did not mention value 'not-a-number': " << msg;
    }
}

#include "SpccCandidateMessage.h"
#include <msgpack.hpp>
#include <openssl/sha.h>

namespace {
std::string sha256_hex(const std::vector<std::uint8_t>& data) {
    unsigned char digest[SHA256_DIGEST_LENGTH];
    SHA256(data.data(), data.size(), digest);
    static const char* hex = "0123456789abcdef";
    std::string out(SHA256_DIGEST_LENGTH * 2, '\0');
    for (int i = 0; i < SHA256_DIGEST_LENGTH; ++i) {
        out[2*i]   = hex[digest[i] >> 4];
        out[2*i+1] = hex[digest[i] & 0xF];
    }
    return out;
}
}

TEST(SpccCandidateMessageTest, EncodesEnvelopeOffline) {
    SpccCandidateMessage msg;
    msg.producer_id = "pss-test-node-01";
    msg.spccl.scheduling_block_id = "sbi-1";
    msg.spccl.beam_id = "beam-7";
    msg.spccl.mjd = 60000.5;
    msg.spccl.dm = 56.7f;
    msg.spccl.width = 0.001f;
    msg.spccl.snr = 12.3f;
    msg.payload.assign(1024, 0xAB);

    auto encoded = msg.encode();
    EXPECT_EQ(encoded.key, "sbi-1:beam-7");

    ASSERT_GE(encoded.value.size(), 4u);
    std::uint32_t env_len =
        (std::uint32_t(encoded.value[0]) << 24) |
        (std::uint32_t(encoded.value[1]) << 16) |
        (std::uint32_t(encoded.value[2]) << 8)  |
        (std::uint32_t(encoded.value[3]));
    ASSERT_EQ(encoded.value.size(), 4 + env_len + msg.payload.size());

    msgpack::object_handle oh = msgpack::unpack(
        reinterpret_cast<const char*>(encoded.value.data() + 4), env_len);
    msgpack::object obj = oh.get();
    ASSERT_EQ(obj.type, msgpack::type::MAP);

    std::map<std::string, msgpack::object> fields;
    for (std::uint32_t i = 0; i < obj.via.map.size; ++i) {
        fields[obj.via.map.ptr[i].key.as<std::string>()] =
            obj.via.map.ptr[i].val;
    }
    EXPECT_EQ(fields.at("schema_version").as<std::uint8_t>(), 1);
    EXPECT_EQ(fields.at("candidate_type").as<std::string>(), "single_pulse");
    EXPECT_EQ(fields.at("payload_mode").as<std::string>(), "inline");
    EXPECT_EQ(fields.at("producer_id").as<std::string>(), "pss-test-node-01");
    EXPECT_EQ(fields.at("payload_size_bytes").as<std::uint32_t>(),
              std::uint32_t(msg.payload.size()));
    EXPECT_EQ(fields.at("checksum_sha256").as<std::string>(),
              sha256_hex(msg.payload));
    EXPECT_EQ(fields.at("message_id").as<std::string>().size(), 36u);
    EXPECT_GT(fields.at("timestamp_utc").as<std::uint64_t>(), 0u);

    msgpack::object spccl = fields.at("spccl");
    ASSERT_EQ(spccl.type, msgpack::type::MAP);
    std::map<std::string, msgpack::object> sf;
    for (std::uint32_t i = 0; i < spccl.via.map.size; ++i) {
        sf[spccl.via.map.ptr[i].key.as<std::string>()] =
            spccl.via.map.ptr[i].val;
    }
    EXPECT_EQ(sf.at("scheduling_block_id").as<std::string>(), "sbi-1");
    EXPECT_EQ(sf.at("beam_id").as<std::string>(), "beam-7");
    EXPECT_DOUBLE_EQ(sf.at("mjd").as<double>(), 60000.5);
    EXPECT_FLOAT_EQ(sf.at("dm").as<float>(), 56.7f);
}

TEST(SpccCandidateMessageTest, ChecksumChangesWithPayload) {
    SpccCandidateMessage a, b;
    a.spccl.scheduling_block_id = b.spccl.scheduling_block_id = "x";
    a.spccl.beam_id = b.spccl.beam_id = "y";
    a.payload = {1, 2, 3};
    b.payload = {1, 2, 4};
    auto ea = a.encode();
    auto eb = b.encode();
    EXPECT_NE(ea.value, eb.value);
}

TEST(SpccCandidateMessageTest, GeneratesUniqueMessageIdsPerEncode) {
    SpccCandidateMessage msg;
    msg.spccl.scheduling_block_id = "x";
    msg.spccl.beam_id = "y";
    msg.payload = {0};
    auto e1 = msg.encode();
    auto e2 = msg.encode();
    EXPECT_NE(e1.value, e2.value);
}
