FROM apache/spark:3.5.1-python3

USER root

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /opt/spark/work-dir

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/batch/jobs/ ./jobs/

USER spark

ENTRYPOINT ["/opt/entrypoint.sh"]
