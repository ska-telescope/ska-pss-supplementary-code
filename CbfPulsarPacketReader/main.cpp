#include "CbfPsrPacket.h"
#include <iostream>
#include <fstream>
#include <vector>
#include <sstream>

template<class T>
char* as_bytes(T& i)
{
  void* addr = &i;
  return static_cast<char *>(addr);
}

struct PssLowTraits
{
    static constexpr uint32_t number_of_channels = 7776;
    static constexpr uint32_t number_of_channels_per_packet = 9;
    static constexpr uint32_t number_of_samples_per_packet = 128;
    static constexpr uint32_t size_of_packet = 4736;
    typedef int8_t PacketDataType;
};

int main()
{
    typedef typename ska::cbf_psr_interface::CbfPsrPacket<int8_t, 128, 9> PacketType;

    std::ifstream packet_file("packet_data.dat", std::ios::binary);

    std::vector<PacketType> buffer(1);

    packet_file.read(as_bytes(buffer[0]), 3664);

    auto const& header = buffer[0].header();

    std::cout<<"First Channel Frequency: "<<buffer[0].first_channel_frequency()<<"\n";
    std::cout<<"Time stamp in seconds: "<<buffer[0].timestamp_seconds()<<"\n";
    std::cout<<"Time stamp in attoseconds: "<<buffer[0].timestamp_attoseconds()<<"\n";
    std::cout<<"Channel seperation: "<<(buffer[0].channel_separation()/1000000.0)<<" KHz\n";
    std::cout<<"First Channel number: "<<buffer[0].first_channel_number()<<"\n";
    std::cout<<"Beam number: "<<buffer[0].beam_number()<<"\n";
    std::cout<<"data precision: "<<(int)buffer[0].data_precision()<<" bits\n";
    std::cout<<"scan id: "<<buffer[0].scan_id()<<"\n";
    std::cout<<"packet sequence number "<<header.packet_sequence_number()<<"\n";
    std::cout<<"channels per packet "<<header.channels_per_packet()<<"\n";
    std::cout<<"valid channels per packet "<<header.valid_channels_per_packet()<<"\n";
    std::stringstream ss;
    ss << std::hex << header.magic_word(); // int decimal_value
    std::string res ( ss.str() );
        std::cout<<"magic word 0x"<<res<<" \n";
    std::cout<<"number of power samples averaged: "<<(int)header.number_of_power_samples_averaged()<<"\n";
    std::cout<<"number of time samples weight: "<<(int)header.number_of_time_samples_weight()<<"\n";
    std::cout<<"beamformer version: "<<header.beamformer_version()<<"\n";
    std::cout<<"scale0: "<<header.scale(0)<<"\n";
    std::cout<<"scale1: "<<header.scale(1)<<"\n";
    std::cout<<"scale2: "<<header.scale(2)<<"\n";
    std::cout<<"scale3: "<<header.scale(3)<<"\n";
    std::cout<<"Valid channels per packet: "<<header.valid_channels_per_packet()<<"\n";
}