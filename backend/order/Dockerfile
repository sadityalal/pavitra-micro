# ---------- Stage 1: Build dependencies ----------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install only what’s required to build Python packages
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements first (improves Docker layer caching)
COPY backend/order/requirements.txt .

# Install Python dependencies into user-local directory
RUN pip install --no-cache-dir --user -r requirements.txt


# ---------- Stage 2: Runtime ----------
FROM python:3.11-slim

WORKDIR /app

# Install minimal runtime tools if needed (curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy backend code
COPY backend/order/ /app/order/
COPY backend/shared/ /app/shared/
COPY backend/__init__.py /app/

# Copy Python dependencies from builder image
COPY --from=builder /root/.local /home/appuser/.local

# Set environment variables
ENV PYTHONPATH=/app \
    PATH=/home/appuser/.local/bin:$PATH \
    PORT=8003

# Create a non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8003

# Optional healthcheck (if /health route exists)
HEALTHCHECK CMD curl --fail http://localhost:8003/health || exit 1

CMD ["uvicorn", "order.main:app", "--host", "0.0.0.0", "--port", "8003"]
