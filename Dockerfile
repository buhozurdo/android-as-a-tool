# ==============================================================================
# Android-MCP Production Multi-Stage Dockerfile
# Optimized for minimal image size, zero-root security, and high performance.
# ==============================================================================

# Stage 1: Build & Dependency Resolution
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ ./src/

RUN pip install --no-cache-dir --prefix=/install .

# Stage 2: Hardened Runtime Container
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="Android-MCP" \
      org.opencontainers.image.description="Universal Android Control for AI Agents via Model Context Protocol (MCP) and ADB" \
      org.opencontainers.image.version="0.5.0" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/buhozurdo/android-as-a-tool"

# Install ADB client and clean up in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    android-tools-adb \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root security: create unprivileged user & group
RUN groupadd -g 10001 mcpuser && \
    useradd -u 10001 -g mcpuser -m -s /bin/bash mcpuser

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy source code, guardrails, skills, and configuration
COPY src/ /app/src/
COPY guardrails/ /app/guardrails/
COPY skills/ /app/skills/
COPY pyproject.toml /app/

# Environment configuration
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src:/app \
    ADB_HOST=localhost \
    ADB_PORT=5555

# Ensure app ownership
RUN chown -R mcpuser:mcpuser /app

USER mcpuser

# FastMCP runs over stdio by default for LLM agent integration
ENTRYPOINT ["android-mcp"]
