# ---------- Stage 1: Build dependencies ----------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install compiler for building any Python packages that require it
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements first (improves caching)
COPY backend/user/requirements.txt .

# Install dependencies into a local user directory
RUN pip install --no-cache-dir --user -r requirements.txt


# ---------- Stage 2: Runtime ----------
FROM python:3.11-slim

WORKDIR /app

# Install minimal runtime tools
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY backend/user/ /app/user/
COPY backend/shared/ /app/shared/
COPY backend/__init__.py /app/

# Copy installed Python dependencies from builder image
COPY --from=builder /root/.local /home/appuser/.local

# Set environment variables
ENV PYTHONPATH=/app \
    PATH=/home/appuser/.local/bin:$PATH \
    PORT=8004

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8004

# Optional healthcheck (if /health endpoint exists)
HEALTHCHECK CMD curl --fail http://localhost:8004/health || exit 1

CMD ["uvicorn", "user.main:app", "--host", "0.0.0.0", "--port", "8004"]
