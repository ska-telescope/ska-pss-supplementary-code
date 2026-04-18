#include "KafkaProducer.h"

#include <librdkafka/rdkafka.h>

#include <iostream>
#include <stdexcept>
#include <string>

namespace {
void set_conf(rd_kafka_conf_t* conf, const char* k, const std::string& v) {
    char errstr[512];
    if (rd_kafka_conf_set(conf, k, v.c_str(), errstr, sizeof errstr)
        != RD_KAFKA_CONF_OK) {
        throw std::runtime_error(std::string("rd_kafka_conf_set ") + k
                                 + ": " + errstr);
    }
}
}

KafkaProducer::KafkaProducer(const KafkaProducerConfig& cfg)
    : topic_(cfg.topic)
{
    rd_kafka_conf_t* conf = rd_kafka_conf_new();
    set_conf(conf, "bootstrap.servers",  cfg.bootstrap_servers);
    set_conf(conf, "client.id",          cfg.producer_id);
    set_conf(conf, "acks",               cfg.acks);
    set_conf(conf, "retries",            std::to_string(cfg.retries));
    set_conf(conf, "linger.ms",          std::to_string(cfg.linger_ms));
    set_conf(conf, "compression.type",   cfg.compression_type);
    set_conf(conf, "message.max.bytes",  std::to_string(cfg.message_max_bytes));
    rd_kafka_conf_set_opaque(conf, this);
    rd_kafka_conf_set_dr_msg_cb(conf, &KafkaProducer::delivery_report_cb);

    char errstr[512];
    rk_ = rd_kafka_new(RD_KAFKA_PRODUCER, conf, errstr, sizeof errstr);
    if (!rk_) {
        // conf is owned by rd_kafka_new on success; on failure we must
        // destroy it ourselves.
        rd_kafka_conf_destroy(conf);
        throw std::runtime_error(std::string("rd_kafka_new: ") + errstr);
    }
}

KafkaProducer::~KafkaProducer() {
    if (rk_) {
        rd_kafka_resp_err_t err = rd_kafka_flush(rk_, 2000);
        if (err != RD_KAFKA_RESP_ERR_NO_ERROR) {
            std::cerr << "KafkaProducer destructor flush did not drain in 2s: "
                      << rd_kafka_err2str(err) << "\n";
        }
        rd_kafka_destroy(rk_);
    }
}

bool KafkaProducer::send(const SpccCandidateMessage& msg) {
    return send(msg.encode());
}

bool KafkaProducer::send(const EncodedMessage& enc) {
    // Safe: RD_KAFKA_MSG_F_COPY makes librdkafka copy the buffers immediately,
    // so it never writes through the pointers we hand it.
    rd_kafka_resp_err_t err = rd_kafka_producev(
        rk_,
        RD_KAFKA_V_TOPIC(topic_.c_str()),
        RD_KAFKA_V_KEY(const_cast<char*>(enc.key.data()), enc.key.size()),
        RD_KAFKA_V_VALUE(const_cast<std::uint8_t*>(enc.value.data()), enc.value.size()),
        RD_KAFKA_V_MSGFLAGS(RD_KAFKA_MSG_F_COPY),
        RD_KAFKA_V_END);
    if (err != RD_KAFKA_RESP_ERR_NO_ERROR) {
        last_err_.store(static_cast<int>(err));
        std::cerr << "produce failed: " << rd_kafka_err2str(err) << "\n";
        return false;
    }
    rd_kafka_poll(rk_, 0);
    return true;
}

bool KafkaProducer::flush(int timeout_ms) {
    last_err_.store(0);
    rd_kafka_resp_err_t err = rd_kafka_flush(rk_, timeout_ms);
    if (err != RD_KAFKA_RESP_ERR_NO_ERROR) {
        last_err_.store(static_cast<int>(err));
        return false;
    }
    return last_err_.load() == 0;
}

void KafkaProducer::delivery_report_cb(rd_kafka_s* /*rk*/,
                                       const rd_kafka_message_s* rkmessage,
                                       void* opaque)
{
    auto* self = static_cast<KafkaProducer*>(opaque);
    if (rkmessage->err) {
        self->last_err_.store(static_cast<int>(rkmessage->err));
        std::cerr << "delivery failed: "
                  << rd_kafka_err2str(rkmessage->err) << "\n";
    }
}
