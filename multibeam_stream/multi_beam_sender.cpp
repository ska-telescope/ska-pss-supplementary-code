#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>
#include <cerrno>

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

#include "CbfPsrPacket.h"

using BeamformerPacketLow = CbfPsrPacket<int8_t, 16, 54>;
// Verify these assumptions when adapting this sender or its receiver.
// - Packet layout uses 16 time samples and 54 channels per packet.
// - Channel separation is stored in millihertz; BANDWIDTH_MHZ is converted
//   from MHz before dividing by NUMBER_OF_CHANNELS.
// - packets_per_frame controls when the channel number wraps and packet count
//   advances. The 54-sample increment below is the time-step per frame.
// - Payload data is simulated random noise stored in a reusable buffer.
// - PACKET_INTERVAL_NS is the target interval per packet; each generated
//   packet is sent to every beam before the counter advances.
// - The default source and destination IPs are environment-specific. 


/// This is the starting port for beam 1. Beam 1+x will go to port 34345+x
constexpr unsigned BASE_PORT = 34345;
// This is the assumed number of channels
constexpr uint32_t NUMBER_OF_CHANNELS = 8208;
/// This is the channels-per-packet number
constexpr std::size_t CHANNELS_PER_PACKET = 54;
/// This is the frequency in the first channel
constexpr double FIRST_FREQUENCY_HZ = 250.0 * 1000000.0;
/// This is the assumed bandwidth
constexpr double BANDWIDTH_MHZ = 105.0;

constexpr long PACKET_INTERVAL_NS = 7275;
constexpr std::size_t PAYLOAD_BYTES = 3456;
constexpr std::size_t BUFFER_BYTES = 537919488;

// Add nanoseconds and normalize the timespec.
void add_nsec(timespec& value, long nsec)
{
    value.tv_nsec += nsec;
    value.tv_sec += value.tv_nsec / 1000000000L;
    value.tv_nsec %= 1000000000L;

    if (value.tv_nsec < 0)
    {
        --value.tv_sec;
        value.tv_nsec += 1000000000L;
    }
}

void create_buffer(std::vector<int8_t>& buffer)
{
    const unsigned seed = static_cast<unsigned>(
        std::chrono::high_resolution_clock::now()
            .time_since_epoch()
            .count());

    std::default_random_engine generator(seed);
    std::normal_distribution<double> distribution(0.0, 20.0);

    for (std::size_t i = 0; i < buffer.size(); ++i)
    {
        // Clamp before converting to int8_t.
        const double noise =
    std::max(-128.0, std::min(127.0, distribution(generator)));

        buffer[i] = static_cast<int8_t>(noise);
    }
}

void next(
    BeamformerPacketLow& packet,
    unsigned long counter,
    const std::vector<int8_t>& buffer)
{
    constexpr std::size_t packets_per_frame =
        NUMBER_OF_CHANNELS / CHANNELS_PER_PACKET;

    // Preserve the original packet metadata calculations.
    packet.packet_count(counter / packets_per_frame);

    packet.first_channel_number(
        (counter % packets_per_frame) * CHANNELS_PER_PACKET);

    packet.period_numerator(1728);
    packet.period_denominator(25);

    packet.samples_since_ska_epoch(
        54 * (counter / packets_per_frame));

    packet.magic_word(3199074029U);
    packet.scan_id(1);
    packet.set_unit_weights();

    packet.channel_separation(
        static_cast<uint32_t>(
            (BANDWIDTH_MHZ / static_cast<double>(NUMBER_OF_CHANNELS)) * 1e9));

    packet.first_channel_frequency(
        FIRST_FREQUENCY_HZ +
        (packet.channel_separation() / 1000.0) *
            packet.first_channel_number());

    const std::size_t number_of_packets =
        buffer.size() / PAYLOAD_BYTES;

    const std::size_t offset =
        (counter % number_of_packets) * PAYLOAD_BYTES;

    std::copy_n(
        buffer.begin() + offset,
        PAYLOAD_BYTES,
        packet.begin());
}

// Automatically close the socket when leaving scope.
class SocketGuard
{
public:
    explicit SocketGuard(int fd) : fd_(fd) {}

    ~SocketGuard()
    {
        if (fd_ >= 0)
            ::close(fd_);
    }

    SocketGuard(const SocketGuard&) = delete;
    SocketGuard& operator=(const SocketGuard&) = delete;

private:
    int fd_;
};

int run(int argc, char* argv[])
{
    // Usage:
    // ./multi_beam_sender <number_of_beams> [destination_ip] [source_ip]
    //
    // Examples:
    // ./multi_beam_sender 2 (starts 2 beams pss01-> pss02 at SKA/TOPIC)
    // ./multi_beam_sender 4 10.0.136.10 10.0.136.11

    constexpr unsigned max_beams = 65535 - BASE_PORT + 1;

    if (argc < 2 || argc > 4)
    {
        std::cerr
            << "Usage: " << argv[0]
            << " <number_of_beams> [destination_ip] [source_ip]\n";

        return EXIT_FAILURE;
    }

    const std::string argument(argv[1]);

    if (argument.empty() ||
        argument.find_first_not_of("0123456789") != std::string::npos)
    {
        throw std::invalid_argument(
            "number_of_beams must be a positive integer");
    }

    const unsigned long requested_beams = std::stoul(argument);

    if (requested_beams == 0 || requested_beams > max_beams)
    {
        throw std::out_of_range(
            "number_of_beams must be between 1 and " +
            std::to_string(max_beams));
    }

    const unsigned number_of_beams =
        static_cast<unsigned>(requested_beams);

    const char* destination_ip =
        /// the default here is to-pss-01 (on pss-02 at SKA/TOPIC) 
        /// IP (to listen to) at destination 
        argc >= 3 ? argv[2] : "192.168.1.1";

    const char* source_ip =
        /// the default here is to-pss-02 (on pss-01 at SKA/TOPIC) 
        /// IP (to stream to) at source
        argc >= 4 ? argv[3] : "192.168.1.0";

    sockaddr_in source_address{};
    source_address.sin_family = AF_INET;

    // Let the kernel choose an ephemeral source port.
    source_address.sin_port = htons(0);

    if (inet_pton(
            AF_INET,
            source_ip,
            &source_address.sin_addr) != 1)
    {
        throw std::invalid_argument("Invalid source IPv4 address");
    }

    in_addr destination_address{};

    if (inet_pton(
            AF_INET,
            destination_ip,
            &destination_address) != 1)
    {
        throw std::invalid_argument("Invalid destination IPv4 address");
    }

    // Each beam uses the same destination IP and a different UDP port.
    std::vector<sockaddr_in> destinations(number_of_beams);

    for (unsigned beam = 0; beam < number_of_beams; ++beam)
    {
        destinations[beam].sin_family = AF_INET;
        destinations[beam].sin_addr = destination_address;

        destinations[beam].sin_port =
            htons(static_cast<uint16_t>(BASE_PORT + beam));
    }

    const int sock_fd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);

    if (sock_fd < 0)
    {
        throw std::runtime_error(
            std::string("socket(): ") + strerror(errno));
    }

    SocketGuard socket_guard(sock_fd);

    if (::bind(
            sock_fd,
            reinterpret_cast<const sockaddr*>(&source_address),
            sizeof(source_address)) < 0)
    {
        throw std::runtime_error(
            std::string("bind(): ") + strerror(errno));
    }

    int send_buffer_size = 16 * 1024 * 1024;

    if (setsockopt(
            sock_fd,
            SOL_SOCKET,
            SO_SNDBUF,
            &send_buffer_size,
            sizeof(send_buffer_size)) < 0)
    {
        throw std::runtime_error(
            std::string("setsockopt(): ") + strerror(errno));
    }

    std::vector<int8_t> buffer(BUFFER_BYTES);

    std::cout << "Creating buffer\n" << std::flush;
    create_buffer(buffer);
    std::cout << "Done creating buffer\n";

    std::cout
        << "Source IP: " << source_ip << '\n'
        << "Destination IP: " << destination_ip << '\n'
        << "Number of beams: " << number_of_beams << '\n'
        << "First frequency: " << FIRST_FREQUENCY_HZ / 1000000.0 << " MHz\n"
        << "Bandwidth: " << BANDWIDTH_MHZ << " MHz\n"
        << "Number of channels: " << NUMBER_OF_CHANNELS << '\n'
        << "Channels per packet: " << CHANNELS_PER_PACKET << '\n'
        << "Target packet interval per beam: "
        << PACKET_INTERVAL_NS << " ns\n";

    for (unsigned beam = 0; beam < number_of_beams; ++beam)
    {
        std::cout
            << "Beam " << beam + 1
            << " -> " << destination_ip
            << ':' << BASE_PORT + beam << '\n';
    }

    std::cout << "Sending packets. Press Ctrl+C to stop.\n"
              << std::flush;

    BeamformerPacketLow packet{};
    unsigned long counter = 0;

    timespec deadline{};

    if (clock_gettime(CLOCK_MONOTONIC, &deadline) != 0)
    {
        throw std::runtime_error(
            std::string("clock_gettime(): ") + strerror(errno));
    }

    while (true)
    {
        // Generate one packet for this time/channel position.
        // All beams receive identical simulated data.
        next(packet, counter, buffer);

        int sleep_result;

        do
        {
            sleep_result = clock_nanosleep(
                CLOCK_MONOTONIC,
                TIMER_ABSTIME,
                &deadline,
                nullptr);
        }
        while (sleep_result == EINTR);

        // clock_nanosleep returns its error code directly.
        if (sleep_result != 0)
        {
            throw std::runtime_error(
                std::string("clock_nanosleep(): ") +
                strerror(sleep_result));
        }

        // Send one packet to every beam before advancing the counter.
        for (unsigned beam = 0; beam < number_of_beams; ++beam)
        {
            ssize_t sent;

            do
            {
                sent = sendto(
                    sock_fd,
                    reinterpret_cast<const char*>(&packet),
                    sizeof(packet),
                    0,
                    reinterpret_cast<const sockaddr*>(
                        &destinations[beam]),
                    sizeof(destinations[beam]));
            }
            while (sent < 0 && errno == EINTR);

            if (sent < 0)
            {
                const int error = errno;

                throw std::runtime_error(
                    "sendto() for beam " +
                    std::to_string(beam + 1) +
                    ": " + strerror(error));
            }

            if (static_cast<std::size_t>(sent) != sizeof(packet))
            {
                throw std::runtime_error(
                    "Unexpected UDP send size for beam " +
                    std::to_string(beam + 1));
            }
        }

        ++counter;

        // Retain the original absolute-deadline pacing.
        // If sending falls behind, the loop attempts to catch up.
        add_nsec(deadline, PACKET_INTERVAL_NS);
    }
}

int main(int argc, char* argv[])
{
    try
    {
        return run(argc, argv);
    }
    catch (const std::exception& error)
    {
        std::cerr << "Error: " << error.what() << '\n';
        return EXIT_FAILURE;
    }
}
