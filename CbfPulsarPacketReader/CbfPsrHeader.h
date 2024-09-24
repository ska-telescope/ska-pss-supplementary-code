/*
 * The MIT License (MIT)
 *
 * Copyright (c) 2022 The SKA organisation
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

#ifndef SKA_CBF_PSR_INTERFACE_CBFPSRHEADER_H
#define SKA_CBF_PSR_INTERFACE_CBFPSRHEADER_H

#include <cinttypes>

namespace ska {
namespace cbf_psr_interface {

constexpr std::size_t n_stokes_params = 4;

struct CbfPsrHeader
{
    public:
        enum class PacketType { PssLow, PssMid, PstLow, PstMid };

    public:
        /**
         * @brief Magic word used for packet sanity checks.
         * @details In production all packets magic word should coressponds
         * to this number
         */
        static const uint32_t magic_word_value = 25146554;

    public:

        /**
         * @brief A 64-bit unsigned integer Packet Sequence Number (PSN)
         * @details PSN will be used to provide a robust method to detect lost,
         * out of order or dropped packets. Each packet is uniquely
         * identified by the Packet Sequence Number, Beam Number and
         * First channel frequency numbers.
         */
        uint64_t packet_sequence_number() const;
        void packet_sequence_number(uint64_t const& value);

        /**
         * @brief second part of the timestamp 64-bit integer indicating the
         * number of attoseconds since the start of the current
         * integer second.
         */
        uint64_t timestamp_attoseconds() const;
        void timestamp_attoseconds(uint64_t const& value);

        /**
         * @brief First part of the time stamp unsigned 32-bit integer
         * indicating the number of seconds since 0:00:00 on January 1, 1970.
         */
        uint32_t timestamp_seconds() const;
        void timestamp_seconds(uint32_t const& value);

        /**
         * @brief Frequency spacing between channels in the packet
         * in units of mHz
         */
        uint32_t channel_separation() const;
        void channel_separation(uint32_t const& value);

        /**
         * @brief Field will identify the channel centre frequency of the
         * first Channel Number in the packet in units of mHz
         */

        uint64_t first_channel_frequency() const;
        void first_channel_frequency(uint64_t const& value);

        /**
         * @brief First Channel Number in the packet.
         */
        uint32_t first_channel_number() const;
        void first_channel_number(uint32_t const& value);

        /**
         * @brief A 16-bit unsigned integer channels per packet field
         * will identify the range of contiguous frequency channels
         * contained in the packet.
         */
        uint16_t channels_per_packet() const;
        void channels_per_packet(uint16_t const& value);

        /**
         * @brief A 16-bit unsigned integer channels per packet field
         * will identify the range of contiguous frequency channels
         * contained in the packet. For PSS the value is same as the
         * channels_per_packet
         */
        uint16_t valid_channels_per_packet() const;
        void valid_channels_per_packet(uint16_t const& value);

        /**
         * @brief A 16-bit unsigned integer number of time Samples
         * field will identify the number time samples for each
         * frequency channel contained within the packet.
          */
        uint16_t number_of_time_samples() const;
        void number_of_time_samples(uint16_t const& value);

        /**
         * @brief A 16-bit unsigned integer Beam Number will identify
         * the beam to which the data in the packet belongs.
         * @details there are 16 possible beams for PST, 501 for PssLow, and
         * 1500 for PssMid.
        */
        uint16_t beam_number() const;
        void beam_number(uint16_t const& value);

        /**
         * @brief A 32-bit unsigned integer Magic Number field to
         * enable a basic check of the packet contents during decoding.
         * This should match the static const magic_word_value variable.
        */
        uint32_t magic_word() const;
        void magic_word(uint32_t const& value);

        /**
         * @brief Packet Destination (Pkt Dst)
         * @details This field indicates the intended
         * destination (i.e. data processing backend) for the packet
        */
        PacketType packet_destination() const;
        void packet_destination(PacketType const& value);

        /**
         * @brief An 8-bit unsigned integer Data Precision (Data Precs)
         * @details field indicates the number of bits per integer value
         * stored in the Channel/Sample data section of the packet.
        */
        uint8_t data_precision() const;
        void data_precision(uint8_t const& value);

        /**
         * @brief An 8-bit unsigned integer number of power samples averaged
         * @details Only valid for PssMid PacketType. It will identify the
         * number voltage time samples, whose power is averaged, for each
         * time sample in the packet.
        */
        uint8_t number_of_power_samples_averaged() const;
        void number_of_power_samples_averaged(uint8_t const& value);

        /**
         * @brief An 8-bit unsigned integer number of time samples per
         * relative weight field
         * @details Identifies the number of times samples,
         * for each frequency channel, over which a relative weight is
         * calculated. The Number of Time Samples is an
         * integer multiple of the Number of time samples per relative weight.
        */
        uint8_t number_of_time_samples_weight() const;
        void number_of_time_samples_weight(uint8_t const& value);

        /**
         * @brief 8-bit unsigned integer identifying the numerator of
         * oversampling ratio field.
        */
        uint8_t oversampling_ratio_numerator() const;
        void oversampling_ratio_numerator(uint8_t const& value);

        /**
         * @brief 8-bit unsigned integer identifying the denominator of
         * oversampling ratio field.
        */
        uint8_t oversampling_ratio_denominator() const;
        void oversampling_ratio_denominator(uint8_t const& value);

        /**
         * @brief A 16-bit unsigned integer beamformer version field
         * indicates the system version of the CBF beamformer.
         * @details The upper 8-bits represents a major release number, and the
         * lower 8-bits represents a minor release number.
        */

        uint16_t beamformer_version() const;
        void beamformer_version(uint16_t const& value);

        /**
         * @brief A 64-bit unsigned integer scan ID field
         * @details The scan ID is provided
         * by LMC and included by CBF in the packet so that the pulsar
         * processor can independently check the observational parameters
         * of the current beam data.
        */
        uint64_t scan_id() const;
        void scan_id(uint64_t const& value);

        /**
         * @brief 32-bit floats scale fields.
         * @details Value by which the data should be scaled. For PssLow
         * only the first index (indx =0 )should be used for scaling.
         * In case of power average there are four scale values,
         * one for each Stokes Parameter.
         * @param indx corresponds to polarization index [0-3]
        */
        float scale(int const& indx) const;
        void scale(int const& indx, float const& value);

        /**
         * @brief 32-bit floats Offset.
         * @details Four float values
         * to be added to the corresponding Stokes parameters
         * by PSS and is applied before scaling.
         * The offset is set to make the average mean value small.
         * @param indx corresponds to polarization index [0-3]
        */
        float offset(int const& indx) const;
        void offset(int const& indx, float const& value);

    private:
        uint64_t _packet_sequence_number;
        uint64_t _timestamp_attoseconds;
        uint32_t _timestamp_seconds;
        uint32_t _channel_separation;
        uint64_t _first_channel_frequency;
        float _scale[n_stokes_params];
        uint32_t _first_channel_number;
        uint16_t _channels_per_packet;
        uint16_t _valid_channels_per_packet;
        uint16_t _number_of_time_samples;
        uint16_t _beam_number;
        uint32_t _magic_word;
        uint8_t _packet_destination;
        uint8_t _data_precision;
        uint8_t _number_of_power_samples_averaged;
        uint8_t _number_of_time_samples_weight;
        uint8_t _oversampling_ratio_numerator;
        uint8_t _oversampling_ratio_denominator;
        uint16_t _beamformer_version;
        uint64_t _scan_id;
        float _offset[n_stokes_params];
};

} // namespace cbf_psr_interface
} // namespace ska

#include "CbfPsrHeader.cpp"

#endif // SKA_CBF_PSR_INTERFACE_CBFPSRHEADER_H