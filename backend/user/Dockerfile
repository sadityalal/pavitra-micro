FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ /app/

# Create logs directory
RUN mkdir -p /app/logs
RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["python", "user/main.py"]
