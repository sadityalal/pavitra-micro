# ---------- Stage 1: Build dependencies ----------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install only what's needed to compile Python dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better caching
COPY backend/product/requirements.txt .

# Install dependencies into a temporary user-local directory
RUN pip install --no-cache-dir --user -r requirements.txt


# ---------- Stage 2: Runtime ----------
FROM python:3.11-slim

WORKDIR /app

# Install minimal runtime utilities if needed
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy backend code (only what's necessary)
COPY backend/product/ /app/product/
COPY backend/shared/ /app/shared/
COPY backend/__init__.py /app/

# Copy installed Python dependencies from builder image
COPY --from=builder /root/.local /home/appuser/.local

# Set environment variables
ENV PYTHONPATH=/app \
    PATH=/home/appuser/.local/bin:$PATH \
    PORT=8002

# Create a non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8002

# Optional: container health check (if /health exists)
HEALTHCHECK CMD curl --fail http://localhost:8002/health || exit 1

CMD ["uvicorn", "product.main:app", "--host", "0.0.0.0", "--port", "8002"]
