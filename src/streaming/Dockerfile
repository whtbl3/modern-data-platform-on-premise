FROM flink:1.18-java11

USER root

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /opt/flink/usrlib

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/shared_logic/ ./src/shared_logic/
COPY src/streaming/orders_stream.py ./
COPY src/streaming/clickstream_stream.py ./

USER flink
