FROM ubuntu:noble as builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV PATH=/app/.venv/bin:$PATH \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python3.12

RUN set -ex \
    && apt-get update -yq \
    && apt-get install -yq --no-install-recommends \
        python3.12-dev \
        git \
        ca-certificates

RUN --mount=type=cache,target=/root/.cache \
    set -ex \
    && uv venv /app/.venv

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache \
    set -ex \
    && uv sync --frozen --no-install-project

COPY . /src
RUN --mount=type=cache,target=/root/.cache \
    set -ex \
    && uv pip install --python=/app/.venv --no-deps /src

FROM ubuntu:noble

WORKDIR /app

ENV PATH=/app/.venv/bin:$PATH \
    ROOT_DIR=/app

RUN set -ex \
    && apt-get update -yq  \
    && apt-get install -yq --no-install-recommends \
        ca-certificates \
        python3.12 \
        libpython3.12 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app /app
COPY frontend/ ./frontend/

ENTRYPOINT ["python", "-m", "nowplaying"]
STOPSIGNAL SIGINT
