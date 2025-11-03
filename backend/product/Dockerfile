FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

# Copy everything needed
COPY backend/product/ /app/product/
COPY backend/shared/ /app/shared/
COPY backend/__init__.py /app/
ENV PYTHONPATH=/app
# Install dependencies directly
COPY backend/product/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create uploads directory
RUN mkdir -p /app/uploads/products /app/uploads/avatars /app/uploads/categories
RUN chmod -R 755 /app/uploads

RUN useradd --create-home --shell /bin/bash appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8002

CMD ["python", "-m", "uvicorn", "product.main:app", "--host", "0.0.0.0", "--port", "8002"]