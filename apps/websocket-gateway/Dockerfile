# WebSocket Gateway Dockerfile
# Multi-stage build for production optimization

# Build stage
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && update-ca-certificates

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p /app/logs /app/tmp && chown -R appuser:appuser /app

# Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# WebSocket-specific environment variables
ENV WS_LOG_LEVEL=INFO
ENV WS_MAX_CONNECTIONS=10000
ENV WS_TIMEOUT=300

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8002

# Health check with better error handling
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Security and optimization
# Add metadata labels
LABEL maintainer="Cyber Werewolves Team"
LABEL version="1.0.0"
LABEL description="Cyber Werewolves WebSocket Gateway Service"

# Resource limits (can be overridden by docker-compose limits)
# Default command with production settings
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "4", "--log-level", "info"]