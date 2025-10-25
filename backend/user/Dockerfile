FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

# Copy everything needed
COPY backend/user/ /app/user/
COPY backend/shared/ /app/shared/
COPY backend/__init__.py /app/

# Install dependencies directly
COPY backend/user/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --shell /bin/bash appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8004

CMD ["python", "-m", "uvicorn", "user.main:app", "--host", "0.0.0.0", "--port", "8004"]