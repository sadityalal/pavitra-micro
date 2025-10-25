# ---------- Stage 1: Build dependencies ----------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies (for compiling Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (improves build caching)
COPY backend/auth/requirements.txt .

# Install dependencies to a temporary user-local directory
RUN pip install --no-cache-dir --user -r requirements.txt


# ---------- Stage 2: Runtime ----------
FROM python:3.11-slim

WORKDIR /app

# Install minimal runtime utilities only if needed
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy backend application code
COPY backend/auth/ /app/auth/
COPY backend/shared/ /app/shared/
COPY backend/__init__.py /app/

# Copy installed Python dependencies from builder image
COPY --from=builder /root/.local /home/appuser/.local

# Set environment variables
ENV PYTHONPATH=/app \
    PATH=/home/appuser/.local/bin:$PATH \
    PORT=8001

# Create a non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8001

# Optional: healthcheck for production
HEALTHCHECK CMD curl --fail http://localhost:8001/health || exit 1

# ✅ Correct CMD (since main.py is in /app/auth/main.py)
CMD ["uvicorn", "auth.main:app", "--host", "0.0.0.0", "--port", "8001"]
