FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/tmp/uv-cache-podcast-auto-editor \
    PATH=/root/.local/bin:$PATH

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /workspace

COPY pyproject.toml uv.lock README.md README.zh-TW.md ./
COPY podcast_auto_editor ./podcast_auto_editor
COPY tests ./tests

RUN uv sync --group dev

CMD ["uv", "run", "python", "-m", "podcast_auto_editor", "--help"]
