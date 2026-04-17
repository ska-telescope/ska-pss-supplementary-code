#pragma once
#include "KafkaProducerConfig.h"
#include "SpccCandidateMessage.h"

#include <atomic>
#include <string>

struct rd_kafka_s;
struct rd_kafka_conf_s;
struct rd_kafka_message_s;

class KafkaProducer {
public:
    explicit KafkaProducer(const KafkaProducerConfig& cfg);
    ~KafkaProducer();

    KafkaProducer(const KafkaProducer&)            = delete;
    KafkaProducer& operator=(const KafkaProducer&) = delete;
    KafkaProducer(KafkaProducer&&)                 = delete;
    KafkaProducer& operator=(KafkaProducer&&)      = delete;

    // Returns true if the produce call was accepted by librdkafka.
    // Delivery success/failure is signalled via the dr_msg_cb and
    // surfaces through last_error_code()/flush().
    bool send(const SpccCandidateMessage& msg);

    // Blocks up to timeout_ms for outstanding messages to be delivered.
    // Returns true if all delivered successfully.
    bool flush(int timeout_ms);

    int last_error_code() const { return last_err_.load(); }

private:
    static void delivery_report_cb(rd_kafka_s* rk,
                                   const rd_kafka_message_s* rkmessage,
                                   void* opaque);

    std::string topic_;
    rd_kafka_s* rk_ = nullptr;
    std::atomic<int> last_err_{0};
};
