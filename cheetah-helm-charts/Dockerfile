FROM ubuntu:22.04

COPY cheetah*.deb /tmp/cheetah.deb

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y ca-certificates libboost-program-options1.74.0  libboost-filesystem1.74.0 libfftw3-single3 /tmp/cheetah.deb

# Create cheetah user and create credentials
RUN useradd \ 
    --create-home \
    --home-dir /home/cheetah \
    --shell /bin/bash \
    --uid 1001 \
    cheetah

RUN mkdir /tmp/beam1 /tmp/beam2 /tmp/beam3

RUN chmod +x /usr/bin/cheetah_pipeline && \
    chown -R cheetah:cheetah /etc/cheetah

USER cheetah
WORKDIR /home/cheetah

ENTRYPOINT ["/usr/bin/cheetah_pipeline"]
