FROM python:3.11-buster as builder

RUN pip install poetry==1.5.1

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

FROM node:22.3-alpine as frontend-builder

COPY frontend/ /frontend/
WORKDIR /frontend/ym/web-app/

ENV NODE_ENV=production
RUN npm i

ENV NODE_OPTIONS=--openssl-legacy-provider
RUN npm run build

FROM python:3.11-slim-buster as runtime

WORKDIR /app

RUN apt-get update \
    && apt-get install -yq --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=frontend-builder /frontend/ym/web-app/build/ ./frontend/ym/web-app/build/

COPY nowplaying/ ./nowplaying/
COPY main.py .
COPY init.sql .
COPY .env .

ENTRYPOINT ["python", "main.py"]
