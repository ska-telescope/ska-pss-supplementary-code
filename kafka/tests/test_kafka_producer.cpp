#include <gtest/gtest.h>
#include "KafkaProducerConfig.h"
#include "SpccInputLoader.h"
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

#include "KafkaProducer.h"
#include <librdkafka/rdkafka.h>
#include <chrono>
#include <cstdlib>
#include <stdexcept>

namespace {
std::string getenv_or(const char* k, const char* dflt) {
    const char* v = std::getenv(k);
    return v ? std::string(v) : std::string(dflt);
}

std::string unique_topic_name() {
    return "test-spcc-" + std::to_string(::getpid()) + "-"
           + std::to_string(std::chrono::duration_cast<std::chrono::nanoseconds>(
                std::chrono::steady_clock::now().time_since_epoch()).count());
}

struct ConsumerHandle {
    rd_kafka_t* rk = nullptr;
    ~ConsumerHandle() {
        if (rk) {
            rd_kafka_consumer_close(rk);
            rd_kafka_destroy(rk);
        }
    }
};

ConsumerHandle make_consumer(const std::string& brokers,
                             const std::string& topic,
                             const std::string& group)
{
    char errstr[512];
    rd_kafka_conf_t* conf = rd_kafka_conf_new();
    rd_kafka_conf_set(conf, "bootstrap.servers", brokers.c_str(), errstr, sizeof errstr);
    rd_kafka_conf_set(conf, "group.id", group.c_str(), errstr, sizeof errstr);
    rd_kafka_conf_set(conf, "auto.offset.reset", "earliest", errstr, sizeof errstr);
    rd_kafka_conf_set(conf, "enable.auto.commit", "false", errstr, sizeof errstr);
    rd_kafka_conf_set(conf, "fetch.message.max.bytes", "4194304", errstr, sizeof errstr);

    ConsumerHandle h;
    h.rk = rd_kafka_new(RD_KAFKA_CONSUMER, conf, errstr, sizeof errstr);
    if (!h.rk) { rd_kafka_conf_destroy(conf); throw std::runtime_error(errstr); }
    rd_kafka_poll_set_consumer(h.rk);

    rd_kafka_topic_partition_list_t* parts = rd_kafka_topic_partition_list_new(1);
    rd_kafka_topic_partition_list_add(parts, topic.c_str(), RD_KAFKA_PARTITION_UA);
    rd_kafka_subscribe(h.rk, parts);
    rd_kafka_topic_partition_list_destroy(parts);
    return h;
}
}  // namespace

TEST(SpccInputLoaderTest, LoadsRawPayloadBytes) {
    std::string path = "/tmp/kpc_payload_" + std::to_string(::getpid()) + ".bin";
    {
        std::ofstream f(path, std::ios::binary);
        const char bytes[] = {0x01, 0x02, 0x03, 0x04, 0x05};
        f.write(bytes, sizeof bytes);
    }
    auto v = load_payload_bytes(path);
    ASSERT_EQ(v.size(), 5u);
    EXPECT_EQ(v[0], 0x01);
    EXPECT_EQ(v[4], 0x05);
}

TEST(SpccInputLoaderTest, ThrowsOnMissingPayloadFile) {
    EXPECT_THROW(load_payload_bytes("/no/such/blob.bin"), std::runtime_error);
}

TEST(SpccInputLoaderTest, MetaLoaderStubThrows) {
    EXPECT_THROW(load_spccl_meta("/tmp/anything.msgpack"), std::logic_error);
}

TEST(KafkaRoundTrip, SendsAndReceivesSingleMessage) {
    KafkaProducerConfig cfg;
    cfg.bootstrap_servers = getenv_or("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092");
    cfg.topic             = unique_topic_name();

    auto consumer = make_consumer(cfg.bootstrap_servers, cfg.topic,
                                  "test-grp-" + std::to_string(::getpid()));

    SpccCandidateMessage msg;
    msg.producer_id = cfg.producer_id;
    msg.spccl.scheduling_block_id = "sbi-rt";
    msg.spccl.beam_id             = "beam-rt";
    msg.spccl.mjd                 = 60001.25;
    msg.spccl.dm                  = 42.0f;
    msg.spccl.width               = 0.002f;
    msg.spccl.snr                 = 9.5f;
    msg.payload.assign(2300000, 0xCC);

    auto expected_checksum = sha256_hex(msg.payload);

    KafkaProducer prod(cfg);
    ASSERT_TRUE(prod.send(msg));
    ASSERT_TRUE(prod.flush(10000));

    rd_kafka_message_t* rkm = nullptr;
    for (int i = 0; i < 50 && !rkm; ++i) {
        rkm = rd_kafka_consumer_poll(consumer.rk, 1000);
        if (rkm && rkm->err) { rd_kafka_message_destroy(rkm); rkm = nullptr; }
    }
    ASSERT_NE(rkm, nullptr) << "no message received within 50s";

    std::string key(static_cast<const char*>(rkm->key), rkm->key_len);
    EXPECT_EQ(key, "sbi-rt:beam-rt");

    const auto* val = static_cast<const std::uint8_t*>(rkm->payload);
    ASSERT_GE(rkm->len, 4u);
    std::uint32_t env_len =
        (std::uint32_t(val[0]) << 24) | (std::uint32_t(val[1]) << 16) |
        (std::uint32_t(val[2]) << 8)  |  std::uint32_t(val[3]);
    ASSERT_EQ(rkm->len, 4 + env_len + msg.payload.size());

    msgpack::object_handle oh = msgpack::unpack(
        reinterpret_cast<const char*>(val + 4), env_len);
    msgpack::object obj = oh.get();
    std::map<std::string, msgpack::object> fields;
    for (std::uint32_t i = 0; i < obj.via.map.size; ++i)
        fields[obj.via.map.ptr[i].key.as<std::string>()] = obj.via.map.ptr[i].val;

    EXPECT_EQ(fields.at("payload_size_bytes").as<std::uint32_t>(),
              std::uint32_t(msg.payload.size()));
    EXPECT_EQ(fields.at("checksum_sha256").as<std::string>(), expected_checksum);

    rd_kafka_message_destroy(rkm);
}

TEST(KafkaRoundTrip, SurfacesBrokerErrorOnBadConfig) {
    KafkaProducerConfig cfg;
    cfg.bootstrap_servers = "localhost:1";  // closed port
    cfg.topic = "any";
    cfg.retries = 0;

    SpccCandidateMessage msg;
    msg.spccl.scheduling_block_id = "x";
    msg.spccl.beam_id             = "y";
    msg.payload.assign(16, 0);

    KafkaProducer prod(cfg);
    EXPECT_TRUE(prod.send(msg));     // accepted into queue
    EXPECT_FALSE(prod.flush(3000));  // delivery fails
    EXPECT_NE(prod.last_error_code(), 0);
}
