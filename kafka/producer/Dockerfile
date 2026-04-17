# AT4-2180 placeholder producer image. Builds the producer CLI from source.
# SDP provides the broker only; this builder image is ours to own.
FROM ubuntu:24.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential cmake pkg-config git ca-certificates \
        librdkafka-dev libmsgpack-cxx-dev libssl-dev uuid-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY . /src/kafka
RUN cmake -S /src/kafka -B /build -DCMAKE_BUILD_TYPE=Release && \
    cmake --build /build -j

ENTRYPOINT ["/build/producer/kafka_producer_cli"]
CMD ["--config", "/src/kafka/producer/config/producer.conf"]
