# Multi-stage build for Flask Frontend with FFmpeg
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/app/.uv-cache \
    UV_NO_SYNC=1

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libpq-dev \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV package manager
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Create UV cache directory with proper permissions
RUN mkdir -p /app/.uv-cache && chmod 755 /app/.uv-cache

# Install Python dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p app/static/uploads/audio \
    app/static/uploads/media \
    app/static/uploads/embedded \
    instance

# Set proper permissions for upload directories (instance is 777 so mounted volumes work for any user)
RUN chmod 755 app/static/uploads app/static/uploads/audio app/static/uploads/media app/static/uploads/embedded && \
    chmod 777 instance

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Production stage
FROM base AS production

# Create a non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Change ownership of app directory and UV cache
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Start command for production
CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--worker-class", "sync", "--timeout", "120", "--keep-alive", "2", "--max-requests", "1000", "--max-requests-jitter", "100", "main:app"]

# Development stage
FROM base AS development

# Install development dependencies
RUN uv sync --frozen

# Start command for development
CMD ["uv", "run", "python", "main.py"]

# Default to production
FROM production