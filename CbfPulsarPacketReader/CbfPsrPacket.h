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
#ifndef SKA_CBFPSRINTERFACE_CBFPSRPACKET_H
#define SKA_CBFPSRINTERFACE_CBFPSRPACKET_H

#include "CbfPsrHeader.h"
#include <cstdlib>
#include <cstdint>
#include <array>

namespace ska {
namespace cbf_psr_interface {

/**
 * @brief
 *   Interface to packing/unpacking packets from the BeamFormer receptor stream UDP packet
 * @tparam PacketDataType datatype of the time-frequency elements
 * @tparam TimeSamplesPerPacket Number of contiguous time samples in the packet
 * @tparam ChannelsPerPacket Number of contiguous channels in the pacter
 * @details Caution! The template paramers must match the corresponding header values
 *          This is NOT checked internally in this class.
 */


template<typename PacketDataType, unsigned TimeSamplesPerPacket, unsigned ChannelsPerPacket>
class CbfPsrPacket
{

    public:
        typedef struct ska::cbf_psr_interface::CbfPsrHeader PacketHeader;
        typedef typename PacketHeader::PacketType PacketType;
        typedef decltype(std::declval<PacketHeader>().packet_sequence_number()) PacketNumberType;
        typedef decltype(std::declval<PacketHeader>().first_channel_number()) ChannelNumberType;
        typedef decltype(std::declval<PacketHeader>().scan_id()) ScanIdType;
        typedef decltype(std::declval<PacketHeader>().beam_number()) BeamNumberType;
        typedef decltype(std::declval<PacketHeader>().data_precision()) DataPrecisionType;
        typedef decltype(std::declval<PacketHeader>().magic_word()) MagicWordType;
        typedef decltype(std::declval<PacketHeader>().channel_separation()) ChannelSeperationType;
        typedef uint16_t WeightsType;

    public:
        CbfPsrPacket();

        /**
         * @brief the total size of the udp packets header
         */
        constexpr static std::size_t header_size();

        /**
         * @brief the total size in bytes of the channel rcpt
         */
        constexpr static std::size_t payload_size();

        /**
         * @brief the total size in bytes of the channel rcpt
         */
        constexpr static std::size_t data_size();

        /**
         * @brief the total number of time samples in the packet
         */
        static std::size_t  number_of_samples();

        /**
         * @brief number of elements per polarization
         */
        constexpr static std::size_t elements_per_pol();

        /**
         * @brief the total number of samples in the rcpt payload
         */
        constexpr static std::size_t number_of_elements();

       /**
         * @brief the total number of frequencey channels in the rcpt payload
         */
        static std::size_t number_of_channels();

        /**
         * @brief the total size of the packet (header + payload + footer)
         */
        constexpr static std::size_t size();

        /**
         * @brief maximum sequence number possible
         */
        constexpr static PacketNumberType max_sequence_number();

        /**
         * @brief set the type of packet
         */
        void packet_type(PacketHeader::PacketType const);

        /**
         * @brief return the packet type
         */
        PacketHeader::PacketType packet_type() const;

        /**
         * @brief the number of the first channel in the packet
         */
        ChannelNumberType first_channel_number() const;
        void first_channel_number(ChannelNumberType number);

        /**
         * @brief beam id of the packet stream
         */
        BeamNumberType beam_number() const;
        void beam_number(BeamNumberType number);

        /**
         * @brief Magic word used for consistency checks.
         */
        MagicWordType magic_word() const;
        void magic_word(MagicWordType number);

        /**
         * @brief First channel frequency in the packet in MHz
         */
        double first_channel_frequency() const;
        void first_channel_frequency(double value);

        /**
         * @brief channel_separation
         */
        ChannelSeperationType channel_separation() const;
        void channel_separation(ChannelSeperationType number);

        /**
         * @brief Timestamp in seconds
         */
        uint32_t timestamp_seconds() const;
        void timestamp_seconds(uint32_t number);

        /**
         * @brief Timestamp in attoseconds
         */
        uint64_t timestamp_attoseconds() const;
        void timestamp_attoseconds(uint64_t number);

        /**
         * @brief Data precision
         */
        DataPrecisionType data_precision() const;
        void data_precision(DataPrecisionType number);

        /**
         * @brief scan ID of the packet stream
         */
        ScanIdType scan_id() const;
        void scan_id(ScanIdType number);

        /**
         * @brief set the counter in the header
         */
        void packet_count(PacketNumberType);

        /**
         * @brief get the counter info from header
         */
        PacketNumberType packet_count() const;

        /**
         * @brief const Pointers to the begin and end of the data in the packet
         */
        const PacketDataType* begin() const;
        const PacketDataType* end() const;

        /**
         * @brief Pointers to the begin and end of the data in the packet
         */
        PacketDataType* begin();
        PacketDataType* end();

        /**
         * @brief Pointers to the begin and end of the weights in the packet
         */
        const WeightsType* begin_weights() const;
        const WeightsType* end_weights() const;

        /**
         * @brief access to the header object
         */
        CbfPsrHeader const& header() const;

        /**
         * @brief set all weights to unity
         */
        void set_unit_weights();

    private: // static variables
        static constexpr std::size_t _packet_data_size = ChannelsPerPacket*TimeSamplesPerPacket*sizeof(uint8_t)*4;
        static constexpr std::size_t _packet_weights_size = ChannelsPerPacket*sizeof(WeightsType);
        static constexpr std::size_t _packet_data_padding_size = (16-(_packet_data_size%16))%16;
        static constexpr std::size_t _packet_weights_padding_size = (16-(_packet_weights_size%16))%16;
        static const std::size_t _number_of_elements = TimeSamplesPerPacket*ChannelsPerPacket*4;
        static const std::size_t _size = _packet_data_padding_size + _packet_weights_padding_size + _packet_data_size + _packet_weights_size + sizeof(PacketHeader);
        static const std::size_t _number_of_samples = TimeSamplesPerPacket;
        static const std::size_t _number_of_channels = ChannelsPerPacket;

    private:
        PacketHeader _header;
        WeightsType _weights[(_packet_weights_size+_packet_weights_padding_size)/sizeof(WeightsType)];
        PacketDataType _data[(_packet_data_size+_packet_data_padding_size)/sizeof(PacketDataType)];
};


} // namespace cbf_psr_interface
} // namespace ska
#include "CbfPsrPacket.cpp"

#endif // SKA_CBFPSRINTERFACE_CBFPSRPACKET_H