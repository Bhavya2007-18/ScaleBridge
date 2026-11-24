# ScaleBridge Bio Backend - Production Dockerfile
# Domain F Deliverable (Owner: Person 4 - Reporting, DevOps and Quality Lead)

FROM python:3.12-slim AS base

# Install curl for container health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create non-root system user for security hardening
RUN groupadd -g 10001 scalebridge && \
    useradd -u 10001 -g scalebridge -s /bin/bash -m scalebridge

# Copy package requirements and application source
COPY pyproject.toml ./
COPY scalebridge_science ./scalebridge_science
COPY app ./app

# Install package and dependencies
RUN pip install --no-cache-dir -e .

# Create local storage and backup directories with proper permissions
RUN mkdir -p /app/var/storage /app/var/backups && \
    chown -R scalebridge:scalebridge /app

USER scalebridge

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health/live || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
