# Multi-stage build for production
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r app && useradd -r -g app app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/app/.local
COPY --chown=app:app backend/shared/ ./shared/
COPY --chown=app:app backend/product_service/ .

# Set environment variables
ENV PATH=/home/app/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PORT=8000

# Switch to non-root user
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2 --access-log