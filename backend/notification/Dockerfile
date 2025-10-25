# ---------- Stage 1: Build dependencies ----------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build tools (only for dependency compilation)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy only requirements for efficient caching
COPY backend/notification/requirements.txt .

# Install dependencies to user-local directory
RUN pip install --no-cache-dir --user -r requirements.txt


# ---------- Stage 2: Runtime ----------
FROM python:3.11-slim

WORKDIR /app

# Install minimal runtime utilities (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY backend/notification/ /app/notification/
COPY backend/shared/ /app/shared/
COPY backend/__init__.py /app/

# Copy installed dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Set environment variables
ENV PYTHONPATH=/app \
    PATH=/home/appuser/.local/bin:$PATH \
    PORT=8006

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8006

# Optional healthcheck (if /health route exists)
HEALTHCHECK CMD curl --fail http://localhost:8006/health || exit 1

CMD ["uvicorn", "notification.main:app", "--host", "0.0.0.0", "--port", "8006"]
