#include "CbfPsrHeader.h"

namespace ska {
namespace cbf_psr_interface {

inline uint64_t CbfPsrHeader::packet_sequence_number() const
{
    return _packet_sequence_number;
}

inline void CbfPsrHeader::packet_sequence_number(uint64_t const& value)
{
    _packet_sequence_number = value;
}

inline uint64_t CbfPsrHeader::timestamp_attoseconds() const
{
    return _timestamp_attoseconds;
}

inline void CbfPsrHeader::timestamp_attoseconds(uint64_t const& value)
{
    _timestamp_attoseconds = value;
}

inline uint32_t CbfPsrHeader::timestamp_seconds() const
{
    return _timestamp_seconds;
}

inline void CbfPsrHeader::timestamp_seconds(uint32_t const& value)
{
    _timestamp_seconds = value;
}

inline uint32_t CbfPsrHeader::channel_separation() const
{
    return _channel_separation;
}

inline void CbfPsrHeader::channel_separation(uint32_t const& value)
{
    _channel_separation = value;
}

inline uint64_t CbfPsrHeader::first_channel_frequency() const
{
    return _first_channel_frequency;
}

inline void CbfPsrHeader::first_channel_frequency(uint64_t const& value)
{
    _first_channel_frequency = value;
}

inline uint32_t CbfPsrHeader::first_channel_number() const
{
    return _first_channel_number;
}

inline void CbfPsrHeader::first_channel_number(uint32_t const& value)
{
    _first_channel_number = value;
}

inline uint16_t CbfPsrHeader::channels_per_packet() const
{
    return _channels_per_packet;
}

inline void CbfPsrHeader::channels_per_packet(uint16_t const& value)
{
    _channels_per_packet = value;
}

inline uint16_t CbfPsrHeader::valid_channels_per_packet() const
{
    return _valid_channels_per_packet;
}

inline void CbfPsrHeader::valid_channels_per_packet(uint16_t const& value)
{
    _valid_channels_per_packet = value;
}

inline uint16_t CbfPsrHeader::number_of_time_samples() const
{
    return _number_of_time_samples;
}

inline void CbfPsrHeader::number_of_time_samples(uint16_t const& value)
{
    _number_of_time_samples = value;
}

inline uint16_t CbfPsrHeader::beam_number() const
{
    return _beam_number;
}

inline void CbfPsrHeader::beam_number(uint16_t const& value)
{
    _beam_number = value;
}

inline uint32_t CbfPsrHeader::magic_word() const
{
    return _magic_word;
}

inline void CbfPsrHeader::magic_word(uint32_t const& value)
{
    _magic_word = value;
}

inline CbfPsrHeader::PacketType CbfPsrHeader::packet_destination() const
{
    return PacketType(_packet_destination);
}

inline void CbfPsrHeader::packet_destination(CbfPsrHeader::PacketType const& value)
{
    _packet_destination = (uint8_t)value;
}

inline uint8_t CbfPsrHeader::data_precision() const
{
    return _data_precision;
}

inline void CbfPsrHeader::data_precision(uint8_t const& value)
{
    _data_precision = value;
}

inline uint8_t CbfPsrHeader::number_of_power_samples_averaged() const
{
    return _number_of_power_samples_averaged;
}

inline void CbfPsrHeader::number_of_power_samples_averaged(uint8_t const& value)
{
    _number_of_power_samples_averaged = value;
}

inline uint8_t CbfPsrHeader::number_of_time_samples_weight() const
{
    return _number_of_time_samples_weight;
}

inline void CbfPsrHeader::number_of_time_samples_weight(uint8_t const& value)
{
    _number_of_time_samples_weight = value;
}

inline uint8_t CbfPsrHeader::oversampling_ratio_numerator() const
{
    return _oversampling_ratio_numerator;
}

inline void CbfPsrHeader::oversampling_ratio_numerator(uint8_t const& value)
{
    _oversampling_ratio_numerator = value;
}

inline uint8_t CbfPsrHeader::oversampling_ratio_denominator() const
{
    return _oversampling_ratio_denominator;
}

inline void CbfPsrHeader::oversampling_ratio_denominator(uint8_t const& value)
{
    _oversampling_ratio_denominator = value;
}

inline uint16_t CbfPsrHeader::beamformer_version() const
{
    return _beamformer_version;
}

inline void CbfPsrHeader::beamformer_version(uint16_t const& value)
{
    _beamformer_version = value;
}

inline uint64_t CbfPsrHeader::scan_id() const
{
    return _scan_id;
}

inline void CbfPsrHeader::scan_id(uint64_t const& value)
{
    _scan_id = value;
}

inline float CbfPsrHeader::scale(int const& indx) const
{
    return _scale[indx];
}

inline void CbfPsrHeader::scale(int const& indx, float const& value)
{
    _scale[indx] = value;
}

inline float CbfPsrHeader::offset(int const& indx) const
{
    return _offset[indx];
}

inline void CbfPsrHeader::offset(int const& indx, float const& value)
{
    _offset[indx] = value;
}

} // namespace cbf_psr_interface
} // namespace ska