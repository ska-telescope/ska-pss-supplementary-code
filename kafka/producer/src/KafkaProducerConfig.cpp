#include "KafkaProducerConfig.h"
#include <algorithm>
#include <fstream>
#include <stdexcept>
#include <unordered_map>

namespace {
std::string trim(std::string s) {
    auto not_space = [](unsigned char c) { return !std::isspace(c); };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), not_space));
    s.erase(std::find_if(s.rbegin(), s.rend(), not_space).base(), s.end());
    return s;
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
        else if (key == "retries")                       cfg.retries = std::stoi(val);
        else if (key == "linger.ms")                     cfg.linger_ms = std::stoi(val);
        else if (key == "compression.type")              cfg.compression_type = val;
        else if (key == "message.max.bytes")             cfg.message_max_bytes = std::stoul(val);
        else if (key == "synthetic.payload_bytes")       cfg.synthetic_payload_bytes = std::stoul(val);
        else if (key == "synthetic.scheduling_block_id") cfg.synthetic_scheduling_block_id = val;
        else if (key == "synthetic.beam_id")             cfg.synthetic_beam_id = val;
        // unknown keys silently ignored per design
    }
    return cfg;
}
