FROM python:3.12-slim AS builder

ARG UV_VERSION=0.13.5
RUN pip install --no-cache-dir "uv==$UV_VERSION"
ENV UV_PYTHON_DOWNLOADS=never UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev

FROM python:3.12-slim AS final

LABEL org.opencontainers.image.source="https://github.com/jag-k/owntinfoil"
LABEL org.opencontainers.image.description="OwnTinfoil Image"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.authors="Jag_k"
LABEL org.opencontainers.image.url="https://github.com/jag-k/owntinfoil"
LABEL org.opencontainers.image.documentation="https://github.com/jag-k/owntinfoil/wiki"
LABEL org.opencontainers.image.vendor="Jag_k"


ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    NPS_DIR=/nps \
    TORRENT_DIR=/torrents
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY . /app
CMD ["python", "-m", "app"]
