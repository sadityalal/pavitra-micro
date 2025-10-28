Pavitra Trading E-commerce Platform - Technical Documentation

Table of Contents

System Architecture
Frontend Integration Guide
API Reference
Database Schema
Maintenance Procedures
Troubleshooting Guide
Deployment Guide
Monitoring & Logging
System Architecture

Microservices Overview

text
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway    │    │   Auth Service  │
│   (Next.js)     │◄──►│   (Nginx)       │◄──►│   (8001)        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              │
    ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
    │   Product Service│    │   Message Queue  │    │   Order Service │
    │   (8002)        │◄──►│   (RabbitMQ)     │◄──►│   (8003)        │
    └─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              │
    ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
    │   User Service  │    │   Cache Layer    │    │ Payment Service │
    │   (8004)        │◄──►│   (Redis)        │◄──►│   (8005)        │
    └─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              │
    ┌─────────────────┐    ┌──────────────────┐
    │ Notification    │    │   Database       │
    │ Service (8006)  │    │   (MySQL)        │
    └─────────────────┘    └──────────────────┘
Technology Stack

Backend Services:

Framework: FastAPI (Python 3.12)
Database: MySQL 8.0 with connection pooling
Cache: Redis for session and data caching
Message Queue: RabbitMQ for event-driven architecture
Authentication: JWT with Argon2 hashing
Infrastructure:

Containerization: Docker & Docker Compose
Reverse Proxy: Nginx
Logging: Structured JSON logging
Monitoring: Built-in health checks
Frontend Integration Guide

Authentication Flow

1. User Registration

javascript
// Example registration request
const registerUser = async (userData) => {
  const response = await fetch('http://localhost:8001/api/v1/auth/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: userData.email,
      password: userData.password,
      first_name: userData.firstName,
      last_name: userData.lastName,
      country_id: 1
    })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Store token and user data
    localStorage.setItem('auth_token', data.access_token);
    localStorage.setItem('user_roles', JSON.stringify(data.user_roles));
    return data;
  } else {
    throw new Error(data.detail || 'Registration failed');
  }
};
2. User Login

javascript
// Example login request
const loginUser = async (credentials) => {
  const response = await fetch('http://localhost:8001/api/v1/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      login_id: credentials.email,
      password: credentials.password
    })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    localStorage.setItem('auth_token', data.access_token);
    localStorage.setItem('user_roles', JSON.stringify(data.user_roles));
    localStorage.setItem('user_permissions', JSON.stringify(data.user_permissions));
    return data;
  } else {
    throw new Error(data.detail || 'Login failed');
  }
};
3. Authentication Header Helper

javascript
// Helper function for authenticated requests
const getAuthHeaders = () => {
  const token = localStorage.getItem('auth_token');
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  };
};

// Example authenticated request
const fetchUserProfile = async () => {
  const response = await fetch('http://localhost:8004/api/v1/users/profile', {
    headers: getAuthHeaders()
  });
  
  if (response.status === 401) {
    // Token expired, redirect to login
    window.location.href = '/login';
    return;
  }
  
  return await response.json();
};
Product Catalog Integration

1. Fetch Products with Filtering

javascript
const fetchProducts = async (filters = {}) => {
  const queryParams = new URLSearchParams();
  
  // Add filters
  if (filters.category_id) queryParams.append('category_id', filters.category_id);
  if (filters.brand_id) queryParams.append('brand_id', filters.brand_id);
  if (filters.min_price) queryParams.append('min_price', filters.min_price);
  if (filters.max_price) queryParams.append('max_price', filters.max_price);
  if (filters.search) queryParams.append('search', filters.search);
  if (filters.page) queryParams.append('page', filters.page);
  if (filters.page_size) queryParams.append('page_size', filters.page_size);
  
  const response = await fetch(
    `http://localhost:8002/api/v1/products?${queryParams.toString()}`
  );
  
  return await response.json();
};
2. Product Detail Page

javascript
const fetchProductDetail = async (productId) => {
  const response = await fetch(
    `http://localhost:8002/api/v1/products/${productId}`
  );
  
  if (!response.ok) {
    throw new Error('Product not found');
  }
  
  return await response.json();
};

// Alternative: Fetch by slug
const fetchProductBySlug = async (slug) => {
  const response = await fetch(
    `http://localhost:8002/api/v1/products/slug/${slug}`
  );
  
  if (!response.ok) {
    throw new Error('Product not found');
  }
  
  return await response.json();
};
Shopping Cart Integration

1. Add to Cart

javascript
const addToCart = async (productId, quantity = 1) => {
  const response = await fetch('http://localhost:8004/api/v1/users/cart/' + productId, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ quantity })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to add to cart');
  }
  
  return await response.json();
};
2. Get Cart Contents

javascript
const getCart = async () => {
  const response = await fetch('http://localhost:8004/api/v1/users/cart', {
    headers: getAuthHeaders()
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch cart');
  }
  
  return await response.json();
};
3. Update Cart Item

javascript
const updateCartItem = async (cartItemId, quantity) => {
  const response = await fetch(
    `http://localhost:8004/api/v1/users/cart/${cartItemId}`,
    {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify({ quantity })
    }
  );
  
  return await response.json();
};
Order Management Integration

1. Create Order

javascript
const createOrder = async (orderData) => {
  const response = await fetch('http://localhost:8003/api/v1/orders/', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      items: orderData.items,
      shipping_address: orderData.shippingAddress,
      billing_address: orderData.billingAddress,
      payment_method: orderData.paymentMethod,
      customer_note: orderData.customerNote,
      use_gst_invoice: orderData.useGstInvoice,
      gst_number: orderData.gstNumber
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Order creation failed');
  }
  
  return await response.json();
};
2. Fetch User Orders

javascript
const getUserOrders = async (userId, page = 1, pageSize = 10) => {
  const response = await fetch(
    `http://localhost:8003/api/v1/orders/user/${userId}?page=${page}&page_size=${pageSize}`,
    {
      headers: getAuthHeaders()
    }
  );
  
  return await response.json();
};
Payment Integration

1. Initiate Payment

javascript
const initiatePayment = async (paymentData) => {
  const response = await fetch('http://localhost:8005/api/v1/payments/initiate', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      order_id: paymentData.orderId,
      amount: paymentData.amount,
      currency: paymentData.currency || 'INR',
      payment_method: paymentData.paymentMethod,
      gateway: paymentData.gateway
    })
  });
  
  return await response.json();
};
2. Handle Payment Response

javascript
// For Razorpay integration
const loadRazorpayScript = () => {
  return new Promise((resolve) => {
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
};

const openRazorpayCheckout = async (orderData) => {
  const isLoaded = await loadRazorpayScript();
  if (!isLoaded) {
    throw new Error('Razorpay SDK failed to load');
  }

  const options = {
    key: orderData.razorpay_key,
    amount: orderData.amount * 100, // Convert to paise
    currency: orderData.currency,
    order_id: orderData.razorpay_order_id,
    name: 'Pavitra Trading',
    description: 'Order Payment',
    handler: async function (response) {
      // Verify payment on your server
      await verifyPayment(orderData.payment_id, response);
    },
    prefill: {
      name: user.name,
      email: user.email,
      contact: user.phone
    },
    theme: {
      color: '#4CAF50'
    }
  };

  const razorpay = new window.Razorpay(options);
  razorpay.open();
};
API Reference

Common Response Formats

Success Response

json
{
  "success": true,
  "data": { /* response data */ },
  "message": "Operation successful"
}
Error Response

json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
Paginated Response

json
{
  "success": true,
  "data": {
    "items": [ /* array of items */ ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_count": 150,
      "total_pages": 8,
      "has_next": true,
      "has_prev": false
    }
  }
}
Status Codes

Code	Description
200	Success
201	Created
400	Bad Request - Validation error
401	Unauthorized - Authentication required
403	Forbidden - Insufficient permissions
404	Not Found
409	Conflict - Resource already exists
422	Unprocessable Entity
429	Too Many Requests - Rate limit exceeded
500	Internal Server Error
503	Service Unavailable - Maintenance mode
Database Schema

Core Tables Documentation

Users Table

sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    username VARCHAR(50) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    country_id INT,
    preferred_currency VARCHAR(3) DEFAULT 'INR',
    preferred_language VARCHAR(5) DEFAULT 'en',
    avatar_url VARCHAR(500),
    date_of_birth DATE,
    gender ENUM('male', 'female', 'other'),
    telegram_username VARCHAR(100),
    telegram_phone VARCHAR(20),
    whatsapp_phone VARCHAR(20),
    last_login DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_email (email),
    INDEX idx_phone (phone),
    INDEX idx_username (username),
    INDEX idx_created_at (created_at)
);
Products Table

sql
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    sku VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    short_description TEXT,
    description LONGTEXT,
    specification JSON,
    base_price DECIMAL(10,2) NOT NULL,
    compare_price DECIMAL(10,2),
    category_id INT NOT NULL,
    brand_id INT,
    gst_rate DECIMAL(5,2) DEFAULT 18.00,
    is_gst_inclusive BOOLEAN DEFAULT TRUE,
    track_inventory BOOLEAN DEFAULT TRUE,
    stock_quantity INT DEFAULT 0,
    low_stock_threshold INT DEFAULT 5,
    stock_status ENUM('in_stock', 'low_stock', 'out_of_stock', 'on_backorder') DEFAULT 'out_of_stock',
    product_type ENUM('simple', 'variable', 'digital') DEFAULT 'simple',
    weight_grams DECIMAL(8,2),
    main_image_url VARCHAR(500),
    image_gallery JSON,
    status ENUM('draft', 'active', 'inactive', 'archived') DEFAULT 'draft',
    is_featured BOOLEAN DEFAULT FALSE,
    is_trending BOOLEAN DEFAULT FALSE,
    is_bestseller BOOLEAN DEFAULT FALSE,
    view_count INT DEFAULT 0,
    wishlist_count INT DEFAULT 0,
    total_sold INT DEFAULT 0,
    max_cart_quantity INT DEFAULT 10,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (brand_id) REFERENCES brands(id),
    INDEX idx_sku (sku),
    INDEX idx_slug (slug),
    INDEX idx_category (category_id),
    INDEX idx_brand (brand_id),
    INDEX idx_status (status),
    INDEX idx_featured (is_featured),
    INDEX idx_price (base_price)
);
Orders Table

sql
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    shipping_amount DECIMAL(10,2) DEFAULT 0.00,
    tax_amount DECIMAL(10,2) DEFAULT 0.00,
    discount_amount DECIMAL(10,2) DEFAULT 0.00,
    total_amount DECIMAL(10,2) NOT NULL,
    status ENUM('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded') DEFAULT 'pending',
    payment_status ENUM('pending', 'paid', 'failed', 'refunded', 'partially_refunded') DEFAULT 'pending',
    payment_method ENUM('credit_card', 'debit_card', 'upi', 'netbanking', 'cash_on_delivery', 'wallet') NOT NULL,
    shipping_address JSON NOT NULL,
    billing_address JSON,
    customer_note TEXT,
    is_gst_invoice BOOLEAN DEFAULT FALSE,
    gst_number VARCHAR(15),
    paid_at DATETIME,
    cancelled_at DATETIME,
    cancelled_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_order_number (order_number),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
Index Optimization

Critical Indexes for Performance:

sql
-- Add these indexes for better query performance
CREATE INDEX idx_orders_user_status ON orders(user_id, status);
CREATE INDEX idx_products_category_status ON products(category_id, status);
CREATE INDEX idx_products_price_status ON products(base_price, status);
CREATE INDEX idx_users_email_active ON users(email, is_active);
CREATE INDEX idx_payments_order_status ON payment_transactions(order_id, status);
Maintenance Procedures

Regular Maintenance Tasks

1. Database Maintenance

sql
-- Weekly optimization
OPTIMIZE TABLE users, products, orders, order_items, payment_transactions;

-- Clean up old data (run monthly)
DELETE FROM password_history WHERE created_at < DATE_SUB(NOW(), INTERVAL 1 YEAR);
DELETE FROM notification_logs WHERE created_at < DATE_SUB(NOW(), INTERVAL 6 MONTH);
DELETE FROM user_sessions WHERE last_activity < DATE_SUB(NOW(), INTERVAL 1 MONTH);

-- Update statistics
ANALYZE TABLE users, products, orders, order_items;
2. Cache Maintenance

bash
# Clear Redis cache (run as needed)
redis-cli -h redis -a your_password FLUSHDB

# Or clear specific patterns
redis-cli -h redis -a your_password --scan --pattern "user:*" | xargs redis-cli DEL
redis-cli -h redis -a your_password --scan --pattern "product:*" | xargs redis-cli DEL
3. Log Rotation

bash
# Set up log rotation for service logs
sudo logrotate -f /etc/logrotate.d/pavitra-services
Backup Procedures

1. Database Backup

bash
#!/bin/bash
# database_backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/database"
DB_NAME="pavitra_trading"

# Create backup
mysqldump -h mysql -u pavitra_app -papp123 $DB_NAME > $BACKUP_DIR/${DB_NAME}_${DATE}.sql

# Compress backup
gzip $BACKUP_DIR/${DB_NAME}_${DATE}.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: ${DB_NAME}_${DATE}.sql.gz"
2. File Backup

bash
#!/bin/bash
# file_backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/files"
UPLOAD_DIR="/app/uploads"

# Create backup of uploads
tar -czf $BACKUP_DIR/uploads_${DATE}.tar.gz -C $UPLOAD_DIR .

# Keep only last 30 days of backups
find $BACKUP_DIR -name "uploads_*.tar.gz" -mtime +30 -delete

echo "File backup completed: uploads_${DATE}.tar.gz"
Monitoring Scripts

1. Service Health Check

python
#!/usr/bin/env python3
# health_check.py

import requests
import smtplib
from email.mime.text import MIMEText

SERVICES = {
    'auth': 'http://localhost:8001/health',
    'product': 'http://localhost:8002/health',
    'order': 'http://localhost:8003/health',
    'user': 'http://localhost:8004/health',
    'payment': 'http://localhost:8005/health',
    'notification': 'http://localhost:8006/health'
}

def check_service(service_name, url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('status') == 'healthy'
        return False
    except:
        return False

def send_alert(service_name):
    # Implement email/sms alert logic
    print(f"ALERT: Service {service_name} is down!")

def main():
    for service_name, url in SERVICES.items():
        if not check_service(service_name, url):
            send_alert(service_name)

if __name__ == "__main__":
    main()
Troubleshooting Guide

Common Issues and Solutions

1. Database Connection Issues

Symptoms:

"Database connection failed" errors
High response times
Service startup failures
Solutions:

bash
# Check database status
docker exec -it pavitra-mysql mysql -u root -p -e "SHOW STATUS LIKE 'Threads_connected';"

# Check connection pool
docker logs pavitra-auth-service | grep -i "database\|connection"

# Restart database connection
docker-compose restart mysql

# Increase connection pool size if needed
# Edit shared/database.py - increase pool_size
2. Redis Connection Issues

Symptoms:

Cache-related errors
Session login failures
Performance degradation
Solutions:

bash
# Check Redis status
redis-cli -h redis -a your_password PING

# Check memory usage
redis-cli -h redis -a your_password INFO MEMORY

# Clear cache if corrupted
redis-cli -h redis -a your_password FLUSHALL

# Monitor Redis connections
redis-cli -h redis -a your_password INFO CLIENTS
3. RabbitMQ Issues

Symptoms:

Notification failures
Event processing delays
Message queue backups
Solutions:

bash
# Check RabbitMQ status
docker exec pavitra-rabbitmq rabbitmqctl status

# Check queue status
docker exec pavitra-rabbitmq rabbitmqctl list_queues

# Check connections
docker exec pavitra-rabbitmq rabbitmqctl list_connections

# Restart if needed
docker-compose restart rabbitmq
4. Payment Gateway Issues

Symptoms:

Payment failures
Gateway timeouts
Refund processing errors
Solutions:

bash
# Check payment service logs
docker logs pavitra-payment-service

# Verify gateway credentials
docker exec -it pavitra-mysql mysql -u pavitra_app -papp123 pavitra_trading -e "SELECT setting_key, setting_value FROM site_settings WHERE setting_key LIKE '%razorpay%' OR setting_key LIKE '%stripe%';"

# Test gateway connectivity
curl -X GET https://api.razorpay.com/v1/orders \
  -u razorpay_key_id:razorpay_secret
Performance Troubleshooting

1. Slow Database Queries

sql
-- Identify slow queries
SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;

-- Check query performance
EXPLAIN ANALYZE SELECT * FROM products WHERE category_id = 1 AND status = 'active';

-- Optimize problematic tables
OPTIMIZE TABLE products, orders, users;
2. High Memory Usage

bash
# Check container memory usage
docker stats --no-stream

# Check specific service memory
docker exec pavitra-auth-service ps aux --sort=-%mem | head -10

# Monitor Redis memory
redis-cli -h redis -a your_password INFO MEMORY | grep used_memory_human
3. API Response Time Issues

bash
# Monitor API response times
docker logs pavitra-auth-service | grep "response_time\|processing_time"

# Check for rate limiting
redis-cli -h redis -a your_password --scan --pattern "rate_limit:*" | wc -l

# Verify service health
curl -s http://localhost:8001/health | jq '.'
Deployment Guide

Production Deployment

1. Environment Setup

bash
# Create production directory
mkdir -p /opt/pavitra-trading
cd /opt/pavitra-trading

# Clone repository
git clone https://github.com/your-org/pavitra-trading.git .
git checkout production
2. Environment Configuration

env
# .env.production
# Database
DB_HOST=production-mysql
DB_PORT=3306
DB_NAME=pavitra_trading
DB_USER=pavitra_app
DB_PASSWORD=secure_production_password

# Redis
REDIS_HOST=production-redis
REDIS_PASSWORD=secure_redis_password

# JWT
JWT_SECRET=very_secure_jwt_secret_production

# Payment Gateways
RAZORPAY_KEY_ID=prod_razorpay_key
RAZORPAY_SECRET=prod_razorpay_secret
STRIPE_SECRET_KEY=prod_stripe_secret

# SMTP
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=sendgrid_api_key
3. Docker Compose Production

yaml
# docker-compose.production.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/production.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - auth-service
      - product-service
      - order-service
      - user-service
      - payment-service
      - notification-service

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: secure_root_password
      MYSQL_DATABASE: pavitra_trading
      MYSQL_USER: pavitra_app
      MYSQL_PASSWORD: secure_production_password
    volumes:
      - mysql_data:/var/lib/mysql
      - ./backup:/backup
    command: 
      - --default-authentication-plugin=mysql_native_password
      - --innodb-buffer-pool-size=1G
      - --innodb-log-file-size=256M

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass secure_redis_password
    volumes:
      - redis_data:/data

  rabbitmq:
    image: rabbitmq:3-management
    environment:
      RABBITMQ_DEFAULT_USER: admin
      RABBITMQ_DEFAULT_PASS: secure_rabbitmq_password
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq

  # Services with production configurations
  auth-service:
    build: ./backend/auth
    environment:
      - ENVIRONMENT=production
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  # ... other services with similar production configs

volumes:
  mysql_data:
  redis_data:
  rabbitmq_data:
4. Deployment Script

bash
#!/bin/bash
# deploy.sh

echo "Starting production deployment..."

# Pull latest changes
git pull origin production

# Build and start services
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d

# Wait for services to be healthy
echo "Waiting for services to start..."
sleep 30

# Run database migrations if any
docker-compose -f docker-compose.production.yml exec mysql \
  mysql -u pavitra_app -psecure_production_password pavitra_trading -e "
  -- Add any migration scripts here
  "

# Warm up caches
echo "Warming up caches..."
curl -s http://localhost/api/v1/products?page=1 &> /dev/null
curl -s http://localhost/api/v1/categories/all &> /dev/null

echo "Deployment completed successfully!"
SSL Configuration

Nginx SSL Configuration

nginx
# nginx/production.conf
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/private.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    location /api/v1/auth/ {
        proxy_pass http://auth-service:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/v1/products/ {
        proxy_pass http://product-service:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # ... other service routes
}
Monitoring & Logging

Log Management

1. Log Structure

json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "ERROR",
  "service": "auth-service",
  "message": "Database connection failed",
  "module": "database",
  "function": "get_connection",
  "line": 45,
  "user_id": "12345",
  "request_id": "req-abc123",
  "exception": "Connection timeout after 30 seconds"
}
2. Log Rotation Configuration

bash
# /etc/logrotate.d/pavitra-services
/opt/pavitra-trading/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
3. Centralized Logging (Optional)

yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
Performance Monitoring

1. Custom Metrics Collection

python
# shared/monitoring.py
import time
import psutil
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_USERS = Gauge('active_users', 'Currently active users')
DATABASE_CONNECTIONS = Gauge('database_connections', 'Active database connections')

def monitor_request(request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_DURATION.observe(duration)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    return response
2. Health Dashboard

python
# monitoring_dashboard.py
from flask import Flask, jsonify
import requests
import psutil

app = Flask(__name__)

SERVICES = [
    'http://auth-service:8001/health',
    'http://product-service:8002/health',
    # ... other services
]

@app.route('/system-health')
def system_health():
    health_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'system': {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent
        },
        'services': {}
    }
    
    for service_url in SERVICES:
        try:
            response = requests.get(service_url, timeout=5)
            health_data['services'][service_url] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response.elapsed.total_seconds()
            }
        except:
            health_data['services'][service_url] = {
                'status': 'unreachable',
                'response_time': None
            }
    
    return jsonify(health_data)