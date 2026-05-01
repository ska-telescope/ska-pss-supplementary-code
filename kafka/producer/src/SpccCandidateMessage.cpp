#include "SpccCandidateMessage.h"

#include <msgpack.hpp>
#include <openssl/sha.h>
#include <uuid/uuid.h>

#include <chrono>
#include <cstring>
#include <stdexcept>

namespace {

std::string make_uuid4() {
    uuid_t u;
    uuid_generate_random(u);
    char buf[37];
    uuid_unparse_lower(u, buf);
    return std::string(buf);
}

std::uint64_t now_epoch_ms() {
    using namespace std::chrono;
    return duration_cast<milliseconds>(
        system_clock::now().time_since_epoch()).count();
}

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

void pack_envelope(msgpack::sbuffer& buf,
                   const SpccCandidateMessage& m,
                   const std::string& message_id,
                   std::uint64_t ts_ms,
                   const std::string& checksum)
{
    msgpack::packer<msgpack::sbuffer> pk(buf);
    pk.pack_map(9);
    pk.pack(std::string("schema_version"));    pk.pack(std::uint8_t(1));
    pk.pack(std::string("message_id"));        pk.pack(message_id);
    pk.pack(std::string("producer_id"));       pk.pack(m.producer_id);
    pk.pack(std::string("timestamp_utc"));     pk.pack(ts_ms);
    pk.pack(std::string("candidate_type"));    pk.pack(std::string("single_pulse"));
    pk.pack(std::string("payload_mode"));      pk.pack(std::string("inline"));
    pk.pack(std::string("payload_size_bytes"));pk.pack(std::uint32_t(m.payload.size()));
    pk.pack(std::string("checksum_sha256"));   pk.pack(checksum);

    pk.pack(std::string("spccl"));
    pk.pack_map(6);
    pk.pack(std::string("scheduling_block_id")); pk.pack(m.spccl.scheduling_block_id);
    pk.pack(std::string("beam_id"));             pk.pack(m.spccl.beam_id);
    pk.pack(std::string("mjd"));                 pk.pack(m.spccl.mjd);
    pk.pack(std::string("dm"));                  pk.pack(m.spccl.dm);
    pk.pack(std::string("width"));               pk.pack(m.spccl.width);
    pk.pack(std::string("snr"));                 pk.pack(m.spccl.snr);
}

}  // namespace

EncodedMessage SpccCandidateMessage::encode() const {
    if (spccl.scheduling_block_id.empty() || spccl.beam_id.empty()) {
        throw std::invalid_argument(
            "SpccCandidateMessage: scheduling_block_id and beam_id required");
    }

    EncodedMessage out;
    out.key = spccl.scheduling_block_id + ":" + spccl.beam_id;

    const std::string mid = make_uuid4();
    const std::uint64_t ts = now_epoch_ms();
    const std::string cs = sha256_hex(payload);

    msgpack::sbuffer env;
    pack_envelope(env, *this, mid, ts, cs);
    const std::uint32_t env_len = static_cast<std::uint32_t>(env.size());

    out.value.resize(4 + env_len + payload.size());
    out.value[0] = std::uint8_t(env_len >> 24);
    out.value[1] = std::uint8_t(env_len >> 16);
    out.value[2] = std::uint8_t(env_len >> 8);
    out.value[3] = std::uint8_t(env_len);
    std::memcpy(out.value.data() + 4, env.data(), env_len);
    std::memcpy(out.value.data() + 4 + env_len,
                payload.data(), payload.size());
    out.message_id = mid;
    out.timestamp_utc_ms = ts;
    return out;
}
