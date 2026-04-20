#include "SpccInputLoader.h"
#include <fstream>
#include <stdexcept>

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

SpcclOverrides load_spccl_meta(const std::string&) { return {}; }  // filled in Task 2
