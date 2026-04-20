#include "SpccInputLoader.h"
#include <fstream>
#include <sstream>
#include <stdexcept>

#include <msgpack.hpp>

std::vector<std::uint8_t> load_payload_bytes(const std::string& path) {
    std::ifstream f(path, std::ios::binary | std::ios::ate);
    if (!f) throw std::runtime_error("payload file not readable: " + path);
    std::streamsize n = f.tellg();
    f.seekg(0, std::ios::beg);
    std::vector<std::uint8_t> buf(static_cast<std::size_t>(n));
    if (n && !f.read(reinterpret_cast<char*>(buf.data()), n))
        throw std::runtime_error("payload file read failed: " + path);
    return buf;
}

SpcclOverrides load_spccl_meta(const std::string& path) {
    std::ifstream f(path, std::ios::binary | std::ios::ate);
    if (!f) throw std::runtime_error("meta file not readable: " + path);
    std::streamsize n = f.tellg();
    f.seekg(0, std::ios::beg);
    std::string raw(static_cast<std::size_t>(n), '\0');
    if (n && !f.read(raw.data(), n))
        throw std::runtime_error("meta file read failed: " + path);

    msgpack::object_handle oh;
    try {
        oh = msgpack::unpack(raw.data(), raw.size());
    } catch (const std::exception& e) {
        throw std::runtime_error("meta file is not valid msgpack: " + path + ": " + e.what());
    }
    msgpack::object obj = oh.get();
    if (obj.type != msgpack::type::MAP)
        throw std::runtime_error("meta file root is not a msgpack map: " + path);

    SpcclOverrides o;
    for (std::uint32_t i = 0; i < obj.via.map.size; ++i) {
        const auto& kv = obj.via.map.ptr[i];
        if (kv.key.type != msgpack::type::STR) continue;
        std::string k = kv.key.as<std::string>();
        try {
            if      (k == "scheduling_block_id") { o.scheduling_block_id = kv.val.as<std::string>(); o.has_scheduling_block_id = true; }
            else if (k == "beam_id")             { o.beam_id             = kv.val.as<std::string>(); o.has_beam_id             = true; }
            else if (k == "mjd")                 { o.mjd   = kv.val.as<double>(); o.has_mjd   = true; }
            else if (k == "dm")                  { o.dm    = kv.val.as<float>();  o.has_dm    = true; }
            else if (k == "width")               { o.width = kv.val.as<float>();  o.has_width = true; }
            else if (k == "snr")                 { o.snr   = kv.val.as<float>();  o.has_snr   = true; }
        } catch (const std::exception& e) {
            std::ostringstream msg;
            msg << "meta field '" << k << "' in " << path
                << " has unexpected type: " << e.what();
            throw std::runtime_error(msg.str());
        }
    }
    return o;
}
