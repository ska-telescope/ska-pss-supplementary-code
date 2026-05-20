# Placeholder image; will be replaced by SDP-supplied base if/when one arrives.
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml ./
COPY pss_sdp_consumer ./pss_sdp_consumer
COPY config ./config
RUN pip install --no-cache-dir .
ENTRYPOINT ["pss-sdp-consumer", "--config", "/app/config/consumer.conf"]
