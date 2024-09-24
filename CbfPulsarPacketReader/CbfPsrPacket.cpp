/*
 * The MIT License (MIT)
 *
 * Copyright (c) 2016 The SKA organisation
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */
#include "CbfPsrPacket.h"
#include <cassert>
#include <limits>

namespace ska {
namespace cbf_psr_interface {

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::CbfPsrPacket()
{
    _header.number_of_time_samples(TimeSamplesPerPacket);
    _header.channels_per_packet(ChannelsPerPacket);
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
constexpr std::size_t CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::header_size()
{
    return sizeof(PacketHeader);
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
constexpr std::size_t CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::payload_size()
{
    return _packet_data_size+_packet_weights_size+_packet_data_padding_size+_packet_weights_padding_size;
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
constexpr std::size_t CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::data_size()
{
    return _packet_data_size;
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
std::size_t CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::number_of_samples()
{
    return _number_of_samples;
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
constexpr std::size_t CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::number_of_elements()
{
    return _number_of_elements;
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
constexpr std::size_t CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::elements_per_pol()
{
    return TimeSamplesPerPacket*ChannelsPerPacket;
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
constexpr std::size_t CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::size()
{
    return _size;
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
constexpr typename CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::PacketNumberType
CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::max_sequence_number()
{
    return std::numeric_limits<PacketNumberType>::max();
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
std::size_t CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::number_of_channels()
{
    return _number_of_channels;
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
void CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>
::packet_count(PacketNumberType packet_count)
{
    _header.packet_sequence_number(packet_count);
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
typename CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::PacketNumberType
CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::packet_count() const
{
    return _header.packet_sequence_number();
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
void CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::packet_type(PacketHeader::PacketType const type)
{
    _header.packet_destination(static_cast<decltype(std::declval<PacketHeader>().packet_destination())>(type));
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
typename CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::PacketHeader::PacketType
CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::packet_type() const
{
    return _header.packet_destination();
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
const PacketDataType* CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::begin() const
{
    return &_data[0];
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
const PacketDataType* CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::end() const
{
    return &_data[_packet_data_size];
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
PacketDataType* CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::begin()
{
    return &_data[0];
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
PacketDataType* CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::end()
{
    return &_data[_packet_data_size];
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
const typename CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::WeightsType*
CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::begin_weights() const
{
    return &_weights[0];
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
const typename CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::WeightsType*
CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::end_weights() const
{
    return &_weights[_packet_weights_size/sizeof(WeightsType)];
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
void CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::set_unit_weights()
{
    for(unsigned i=0; i<ChannelsPerPacket; ++i) _weights[i]=1;;
    return;
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
typename CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::ChannelNumberType
CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::first_channel_number() const
{
    return _header.first_channel_number();
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
void CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>
::first_channel_number(ChannelNumberType number)
{
    _header.first_channel_number(number);
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
void CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::first_channel_frequency(double value)
{
    _header.first_channel_frequency((uint32_t)(value*1000));
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
double CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::first_channel_frequency() const
{
    return ((double)_header.first_channel_frequency())/1000.0;
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
typename CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::ScanIdType
CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::scan_id() const
{
    return _header.scan_id();
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
void CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::scan_id(ScanIdType number)
{
    _header.scan_id(number);
}


template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
typename CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::BeamNumberType
CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::beam_number() const
{
    return _header.beam_number();
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
void CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>
::beam_number(BeamNumberType number)
{
    _header.beam_number(number);
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
typename CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::MagicWordType
CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::magic_word() const
{
    return _header.magic_word();
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
void CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>
::magic_word(MagicWordType number)
{
    _header.magic_word(number);
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
uint64_t CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>
::timestamp_attoseconds() const
{
    return _header.timestamp_attoseconds();
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
void CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>
::timestamp_attoseconds(uint64_t number)
{
    _header.timestamp_attoseconds(number);
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
uint32_t CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>
::timestamp_seconds() const
{
    return _header.timestamp_seconds();
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
void CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>
::timestamp_seconds(uint32_t number)
{
    _header.timestamp_seconds(number);
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
typename CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::ChannelSeperationType
CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::channel_separation() const
{
    return _header.channel_separation();
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
void CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>
::channel_separation(ChannelSeperationType number)
{
    _header.channel_separation(number);
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
typename CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::DataPrecisionType
CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::data_precision() const
{
    return _header.data_precision();
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
void CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>
::data_precision(DataPrecisionType number)
{
    _header.data_precision(number);
}

template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
CbfPsrHeader const& CbfPsrPacket<PacketDataType, TimeSamplesPerPacket, ChannelsPerPacket>::header() const
{
    return _header;
}

} // namespace cbf_psr_interface
} // namespace ska