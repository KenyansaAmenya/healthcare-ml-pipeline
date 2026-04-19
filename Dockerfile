FROM python:3.11-slim as build

WORKDIR /app

# Install UV
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using UV
RUN uv pip install --system --no-cache -e .

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*


COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

RUN mkdir -p /app/models

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/health')\"

CMD [\"gunicorn\", \"-w\", \"4\", \"-k\", \"uvicorn.workers.UvicornWorker\", \"app.main:app\", \"--bind\", \"0.0.0.0:8000\", \"--timeout\", \"120\"]