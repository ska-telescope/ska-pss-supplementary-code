#include "KafkaProducer.h"
#include "KafkaProducerConfig.h"
#include "SpccCandidateMessage.h"
#include "SpccInputLoader.h"

#include <cstdlib>
#include <ctime>
#include <iomanip>
#include <iostream>
#include <random>
#include <sstream>
#include <string>
#include <vector>

namespace {

struct CliArgs {
    std::string config_path = "producer.conf";
    int  count   = 1;
    bool dry_run = false;
    bool compact = false;
    std::string payload_path;
    std::string meta_path;
};

void print_usage() {
    std::cout
      << "Usage: kafka_producer_cli [--config <path>] [--count N] [--dry-run] [--compact]"
         " [--payload-file <path>] [--meta-file <path>]\n"
      << "  --compact        one-row-per-message table instead of vertical blocks\n"
      << "  --payload-file   read raw payload bytes from <path> instead of synthesising\n"
      << "  --meta-file      override SPCCL fields from msgpack meta-file at <path>\n"
      << "Exit codes: 0 ok, 1 config error, 2 broker error, 3 flush timeout\n";
}

CliArgs parse_args(int argc, char** argv) {
    CliArgs a;
    for (int i = 1; i < argc; ++i) {
        std::string s = argv[i];
        if      (s == "--config" && i + 1 < argc)  a.config_path = argv[++i];
        else if (s == "--count"  && i + 1 < argc)  a.count = std::atoi(argv[++i]);
        else if (s == "--dry-run")                 a.dry_run = true;
        else if (s == "--compact")                 a.compact = true;
        else if (s == "--payload-file" && i + 1 < argc) a.payload_path = argv[++i];
        else if (s == "--meta-file"    && i + 1 < argc) a.meta_path    = argv[++i];
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

SpccCandidateMessage build_message(const KafkaProducerConfig& cfg,
                                   const CliOverrides& ov) {
    SpccCandidateMessage m = build_synthetic(cfg);
    if (ov.has_payload) m.payload = ov.payload;
    if (ov.meta.has_scheduling_block_id) m.spccl.scheduling_block_id = ov.meta.scheduling_block_id;
    if (ov.meta.has_beam_id)             m.spccl.beam_id             = ov.meta.beam_id;
    if (ov.meta.has_mjd)                 m.spccl.mjd                 = ov.meta.mjd;
    if (ov.meta.has_dm)                  m.spccl.dm                  = ov.meta.dm;
    if (ov.meta.has_width)               m.spccl.width               = ov.meta.width;
    if (ov.meta.has_snr)                 m.spccl.snr                 = ov.meta.snr;
    return m;
}

std::string format_iso8601(std::uint64_t ms_since_epoch) {
    std::time_t secs = static_cast<std::time_t>(ms_since_epoch / 1000);
    std::tm tm_utc{};
    gmtime_r(&secs, &tm_utc);
    char buf[32];
    std::strftime(buf, sizeof buf, "%Y-%m-%dT%H:%M:%S", &tm_utc);
    std::ostringstream out;
    out << buf << '.' << std::setw(3) << std::setfill('0') << (ms_since_epoch % 1000) << 'Z';
    return out.str();
}

std::string format_mb(std::size_t bytes) {
    std::ostringstream out;
    out << std::fixed << std::setprecision(2)
        << (static_cast<double>(bytes) / (1024.0 * 1024.0)) << " MB";
    return out.str();
}

void print_block(int index_1based, int total,
                 const SpccCandidateMessage& msg,
                 const EncodedMessage& enc)
{
    std::cout
      << "── message " << index_1based << " of " << total << " ──\n"
      << "  key               : " << enc.key << "\n"
      << "  producer_id       : " << msg.producer_id << "\n"
      << "  message_id        : " << enc.message_id << "\n"
      << "  timestamp_utc     : " << format_iso8601(enc.timestamp_utc_ms) << "\n"
      << "  scheduling_block  : " << msg.spccl.scheduling_block_id << "\n"
      << "  beam_id           : " << msg.spccl.beam_id << "\n"
      << "  mjd               : " << msg.spccl.mjd << "\n"
      << "  dm                : " << msg.spccl.dm << "\n"
      << "  width             : " << msg.spccl.width << "\n"
      << "  snr               : " << msg.spccl.snr << "\n"
      << "  payload_bytes     : " << msg.payload.size()
                                  << "  (" << format_mb(msg.payload.size()) << ")\n"
      << "  envelope_bytes    : " << (enc.value.size() - 4 - msg.payload.size()) << "\n"
      << "  total_value_bytes : " << enc.value.size() << "\n";
}

void print_compact_header() {
    std::cout
      << "  # | key                        | payload   | envelope | total     | message_id\n"
      << "----+----------------------------+-----------+----------+-----------+--------------------------------------\n";
}

void print_compact_row(int index_1based,
                       const SpccCandidateMessage& msg,
                       const EncodedMessage& enc)
{
    const std::size_t env_bytes = enc.value.size() - 4 - msg.payload.size();
    std::cout
      << std::setw(3) << index_1based << " | "
      << std::left << std::setw(26) << enc.key << std::right << " | "
      << std::setw(9) << format_mb(msg.payload.size()) << " | "
      << std::setw(8) << (std::to_string(env_bytes) + " B") << " | "
      << std::setw(9) << format_mb(enc.value.size()) << " | "
      << enc.message_id << "\n";
}

}  // namespace

int main(int argc, char** argv) {
    CliArgs args = parse_args(argc, argv);

    if (args.count <= 0) {
        std::cerr << "invalid --count (" << args.count << "): must be > 0\n";
        return 1;
    }

    KafkaProducerConfig cfg;
    try {
        cfg = KafkaProducerConfig::load(args.config_path);
    } catch (const std::exception& e) {
        std::cerr << "config error: " << e.what() << "\n";
        return 1;
    }

    CliOverrides ov;
    try {
        ov = load_overrides(args.payload_path, args.meta_path);
    } catch (const std::exception& e) {
        std::cerr << "input error: " << e.what() << "\n";
        return 1;
    }

    if (args.dry_run) {
        if (args.compact) print_compact_header();
        for (int i = 0; i < args.count; ++i) {
            auto msg = build_message(cfg, ov);
            auto enc = msg.encode();
            if (args.compact) print_compact_row(i + 1, msg, enc);
            else              print_block(i + 1, args.count, msg, enc);
        }
        return 0;
    }

    try {
        KafkaProducer prod(cfg);
        if (args.compact) print_compact_header();
        for (int i = 0; i < args.count; ++i) {
            auto msg = build_message(cfg, ov);
            auto enc = msg.encode();
            if (!prod.send(enc)) return 2;
            if (args.compact) print_compact_row(i + 1, msg, enc);
            else              print_block(i + 1, args.count, msg, enc);
        }
        if (!prod.flush(10000)) {
            return prod.last_error_code() != 0 ? 2 : 3;
        }
    } catch (const std::exception& e) {
        std::cerr << "broker error: " << e.what() << "\n";
        return 2;
    }
    return 0;
}
