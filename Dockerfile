FROM python:3.11-slim AS builder

WORKDIR /app


COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./


RUN uv venv /app/.venv && \
    uv sync --frozen --no-dev --no-editable && \
    rm -rf /root/.cache/uv


FROM python:3.11-slim

WORKDIR /app


RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && find /usr/lib -name '__pycache__' -type d -exec rm -rf {} + \
    && rm -rf /var/lib/apt/lists/*


COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY ./app ./app
COPY ./models ./models


RUN mkdir -p /app/models


ENV PYTHONPATH=/app

EXPOSE 10000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:10000/health')"

CMD ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:10000", "--timeout", "120"]