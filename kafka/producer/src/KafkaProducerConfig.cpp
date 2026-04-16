#include "KafkaProducerConfig.h"
#include <algorithm>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <unordered_map>

namespace {
std::string trim(std::string s) {
    auto not_space = [](unsigned char c) { return !std::isspace(c); };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), not_space));
    s.erase(std::find_if(s.rbegin(), s.rend(), not_space).base(), s.end());
    return s;
}

int parse_int(const std::string& key, const std::string& val) {
    try {
        return std::stoi(val);
    } catch (const std::exception&) {
        throw std::runtime_error(
            "KafkaProducerConfig: invalid integer for '" + key + "': '" + val + "'");
    }
}

std::uint32_t parse_u32(const std::string& key, const std::string& val) {
    try {
        unsigned long v = std::stoul(val);
        if (v > std::numeric_limits<std::uint32_t>::max()) {
            throw std::runtime_error(
                "KafkaProducerConfig: value out of range for '" + key + "': '" + val + "'");
        }
        return static_cast<std::uint32_t>(v);
    } catch (const std::out_of_range&) {
        throw std::runtime_error(
            "KafkaProducerConfig: value out of range for '" + key + "': '" + val + "'");
    } catch (const std::invalid_argument&) {
        throw std::runtime_error(
            "KafkaProducerConfig: invalid integer for '" + key + "': '" + val + "'");
    }
}
}

KafkaProducerConfig KafkaProducerConfig::load(const std::string& path) {
    std::ifstream in(path);
    if (!in) {
        throw std::runtime_error("KafkaProducerConfig: cannot open " + path);
    }
    KafkaProducerConfig cfg;
    std::string line;
    while (std::getline(in, line)) {
        auto hash = line.find('#');
        if (hash != std::string::npos) line.erase(hash);
        auto eq = line.find('=');
        if (eq == std::string::npos) continue;
        std::string key = trim(line.substr(0, eq));
        std::string val = trim(line.substr(eq + 1));
        if (key.empty()) continue;

        if      (key == "bootstrap.servers")             cfg.bootstrap_servers = val;
        else if (key == "topic")                         cfg.topic = val;
        else if (key == "producer_id")                   cfg.producer_id = val;
        else if (key == "acks")                          cfg.acks = val;
        else if (key == "retries")                       cfg.retries = parse_int(key, val);
        else if (key == "linger.ms")                     cfg.linger_ms = parse_int(key, val);
        else if (key == "compression.type")              cfg.compression_type = val;
        else if (key == "message.max.bytes")             cfg.message_max_bytes = parse_u32(key, val);
        else if (key == "synthetic.payload_bytes")       cfg.synthetic_payload_bytes = parse_u32(key, val);
        else if (key == "synthetic.scheduling_block_id") cfg.synthetic_scheduling_block_id = val;
        else if (key == "synthetic.beam_id")             cfg.synthetic_beam_id = val;
        // unknown keys silently ignored per design
    }
    return cfg;
}
