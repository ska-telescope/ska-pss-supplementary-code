#include "KafkaProducer.h"
#include "KafkaProducerConfig.h"
#include "SpccCandidateMessage.h"

#include <cstdlib>
#include <cstring>
#include <iostream>
#include <random>
#include <string>

namespace {

struct CliArgs {
    std::string config_path = "producer.conf";
    int  count   = 1;
    bool dry_run = false;
};

void print_usage() {
    std::cout
      << "Usage: kafka_producer_cli [--config <path>] [--count N] [--dry-run]\n"
      << "Exit codes: 0 ok, 1 config error, 2 broker error, 3 flush timeout\n";
}

CliArgs parse_args(int argc, char** argv) {
    CliArgs a;
    for (int i = 1; i < argc; ++i) {
        std::string s = argv[i];
        if      (s == "--config" && i + 1 < argc)  a.config_path = argv[++i];
        else if (s == "--count"  && i + 1 < argc)  a.count = std::atoi(argv[++i]);
        else if (s == "--dry-run")                 a.dry_run = true;
        else if (s == "-h" || s == "--help")       { print_usage(); std::exit(0); }
        else { std::cerr << "unknown arg: " << s << "\n"; print_usage(); std::exit(1); }
    }
    return a;
}

SpccCandidateMessage build_synthetic(const KafkaProducerConfig& cfg) {
    SpccCandidateMessage m;
    m.producer_id = cfg.producer_id;
    m.spccl.scheduling_block_id = cfg.synthetic_scheduling_block_id;
    m.spccl.beam_id             = cfg.synthetic_beam_id;
    m.spccl.mjd   = 60000.0;
    m.spccl.dm    = 50.0f;
    m.spccl.width = 0.001f;
    m.spccl.snr   = 10.0f;

    m.payload.resize(cfg.synthetic_payload_bytes);
    std::mt19937 rng{std::random_device{}()};
    for (auto& b : m.payload) b = static_cast<std::uint8_t>(rng() & 0xFF);
    return m;
}

}  // namespace

int main(int argc, char** argv) {
    CliArgs args = parse_args(argc, argv);

    KafkaProducerConfig cfg;
    try {
        cfg = KafkaProducerConfig::load(args.config_path);
    } catch (const std::exception& e) {
        std::cerr << "config error: " << e.what() << "\n";
        return 1;
    }

    if (args.dry_run) {
        auto msg = build_synthetic(cfg);
        auto enc = msg.encode();
        std::cout << "key=" << enc.key
                  << " value_bytes=" << enc.value.size()
                  << " payload_bytes=" << msg.payload.size() << "\n";
        return 0;
    }

    try {
        KafkaProducer prod(cfg);
        for (int i = 0; i < args.count; ++i) {
            auto msg = build_synthetic(cfg);
            if (!prod.send(msg)) return 2;
        }
        if (!prod.flush(10000)) return 3;
    } catch (const std::exception& e) {
        std::cerr << "broker error: " << e.what() << "\n";
        return 2;
    }
    return 0;
}
