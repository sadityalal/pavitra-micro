# Pavitra Trading - Complete Technical Documentation

## Project Architecture
**Microservices E-commerce Platform** with 6 backend services + React frontend

## Services Architecture

### 1. Auth Service (Port: 8001)
**Purpose**: User authentication, registration, JWT management
**Endpoints**:
- `POST /register` - User registration
- `POST /login` - User login
- `GET /users/me` - Get current user profile
- `GET /health` - Service health check

### 2. Product Service (Port: 8002)
**Purpose**: Product catalog, categories, brands, search
**Endpoints**:
- `GET /products` - List products with filters
- `GET /products/{id}` - Get product details
- `GET /categories` - List categories
- `GET /brands` - List brands
- `GET /featured-products` - Featured products

### 3. Order Service (Port: 8003)
**Purpose**: Order management, cart, inventory
**Endpoints**:
- `POST /orders` - Create order
- `GET /orders/{id}` - Get order details
- `GET /users/{id}/orders` - User orders
- `PUT /orders/{id}/status` - Update order status
- `POST /orders/{id}/cancel` - Cancel order

### 4. User Service (Port: 8004)
**Purpose**: User profiles, addresses, wishlist, cart
**Endpoints**:
- `GET /profile` - User profile
- `PUT /profile` - Update profile
- `GET /addresses` - User addresses
- `POST /addresses` - Create address
- `GET /wishlist` - User wishlist
- `POST /wishlist/{product_id}` - Add to wishlist
- `GET /cart` - Shopping cart
- `POST /cart/{product_id}` - Add to cart

### 5. Payment Service (Port: 8005)
**Purpose**: Payment processing, refunds, webhooks
**Endpoints**:
- `POST /initiate` - Initiate payment
- `POST /verify/{id}` - Verify payment
- `POST /refund` - Process refund
- `GET /transactions` - Payment history
- `POST /webhook/razorpay` - Razorpay webhook

### 6. Notification Service (Port: 8006)
**Purpose**: Email, SMS, push notifications
**Endpoints**:
- `POST /email` - Send email
- `POST /sms` - Send SMS
- `POST /push` - Send push notification
- `GET /logs` - Notification logs
- `POST /order/{id}/confirmation` - Order confirmation

## Database Schema - Complete Table Structure

### Users & Authentication
**users**:
- id, uuid, email, password_hash, first_name, last_name, phone
- username, country_id, email_verified, phone_verified, is_active
- avatar_url, last_login, date_of_birth, gender
- preferred_currency, preferred_language
- created_at, updated_at

**user_roles**:
- id, name, description, is_system_role, created_at

**permissions**:
- id, name, description, module, created_at

**role_permissions**:
- id, role_id, permission_id, created_at

**user_role_assignments**:
- id, user_id, role_id, assigned_by, assigned_at

**password_history**:
- id, user_id, password_hash, created_at

### Product Catalog
**products**:
- id, uuid, sku, name, slug, short_description, description
- specification (JSON), base_price, compare_price, cost_price
- gst_rate, hsn_code, is_gst_inclusive, track_inventory
- stock_quantity, low_stock_threshold, allow_backorders
- stock_status, product_type, is_virtual, is_downloadable
- weight_grams, dimensions, main_image_url, image_gallery (JSON)
- category_id, brand_id, status, is_featured, is_trending
- is_bestseller, is_on_sale, is_returnable, return_period_days
- warranty_period_months, meta_title, meta_description
- view_count, wishlist_count, total_sold, created_at, updated_at

**categories**:
- id, uuid, name, name_hindi, slug, description, description_hindi
- meta_title, meta_description, parent_id, image_url, banner_url
- sort_order, is_active, is_featured, gst_slab, hsn_code
- created_at, updated_at

**brands**:
- id, uuid, name, slug, description, logo_url, website_url
- is_active, sort_order, is_indian_brand, brand_origin_country
- created_at, updated_at

**product_attributes**:
- id, name, slug, type, is_visible, sort_order, created_at

**product_attribute_values**:
- id, attribute_id, value, color_code, image_url, sort_order, created_at

**product_variations**:
- id, product_id, sku, price, compare_price, cost_price
- stock_quantity, low_stock_threshold, allow_backorders
- stock_status, weight_grams, dimensions, image_url, is_default
- created_at, updated_at

**variation_attributes**:
- id, variation_id, attribute_id, attribute_value_id

**product_attribute_association**:
- product_id, attribute_value_id, created_at

### Orders & Inventory
**orders**:
- id, uuid, order_number, user_id, subtotal, shipping_amount
- tax_amount, discount_amount, total_amount, status, payment_status
- payment_method, payment_gateway, transaction_id, upi_id
- shipping_method, tracking_number, shipping_address (JSON)
- billing_address (JSON), customer_note, admin_note
- is_gst_invoice, gst_number, paid_at, shipped_at, delivered_at
- cancelled_at, estimated_delivery, created_at, updated_at

**order_items**:
- id, order_id, product_id, variation_id, product_name, product_sku
- product_image, unit_price, quantity, total_price, gst_rate
- gst_amount, variation_attributes (JSON), created_at

**order_history**:
- id, order_id, field_changed, old_value, new_value, changed_by
- change_type, reason, ip_address, user_agent, created_at

**shopping_cart**:
- id, user_id, product_id, variation_id, quantity, cart_data (JSON)
- created_at, updated_at

**stock_movements**:
- id, product_id, variation_id, movement_type, quantity
- stock_before, stock_after, reference_type, reference_id
- reason, performed_by, performed_at

**stock_alerts**:
- id, product_id, variation_id, alert_type, current_stock
- threshold, is_resolved, resolved_at, resolved_by, created_at

### Payments
**payment_transactions**:
- id, uuid, order_id, user_id, amount, currency, payment_method
- gateway_name, gateway_transaction_id, gateway_order_id
- upi_id, upi_transaction_id, vpa, card_last_four, card_type
- card_network, bank_name, bank_transaction_id, wallet_provider
- wallet_transaction_id, status, payment_status, failure_reason
- initiated_at, authorized_at, captured_at, failed_at, refunded_at
- refund_amount, total_refunded, signature, created_at, updated_at

**payment_methods**:
- id, user_id, method_type, is_default, is_active, upi_id
- upi_app, card_last_four, card_type, card_network
- expiry_month, expiry_year, card_holder_name, bank_name
- account_last_four, wallet_provider, wallet_id, token
- created_at, updated_at

**refunds**:
- id, uuid, payment_id, order_id, amount, currency, reason
- status, gateway_refund_id, failure_reason, processed_by
- created_at, updated_at, processed_at

### User Data
**user_addresses**:
- id, user_id, address_type, full_name, phone, country_code
- address_line1, address_line2, landmark, city, state, country
- postal_code, address_type_detail, is_default, created_at, updated_at

**wishlists**:
- id, user_id, product_id, created_at

### Notifications
**notification_logs**:
- id, type, recipient, subject, message, status, template_name
- created_at

### Content & Marketing
**banners**:
- id, title, description, image_url, target_url, banner_type
- sort_order, is_active, start_date, end_date, created_at

**product_reviews**:
- id, uuid, product_id, user_id, order_item_id, rating, title
- comment, review_images (JSON), status, is_verified_purchase
- helpful_count, created_at, updated_at

**review_helpfulness**:
- id, review_id, user_id, is_helpful, created_at

**coupons**:
- id, code, name, description, discount_type, discount_value
- maximum_discount_amount, minimum_order_amount, usage_limit
- usage_limit_per_user, used_count, valid_from, valid_until
- is_active, apply_to, applicable_categories (JSON)
- applicable_products (JSON), created_at, updated_at

**coupon_usage**:
- id, coupon_id, user_id, order_id, discount_amount, used_at

### System & Configuration
**site_settings**:
- id, setting_key, setting_value, setting_type, created_at, updated_at

**countries**:
- id, country_name, country_code, country_code_3, phone_code
- currency_code, currency_symbol, is_active, tax_type
- default_tax_rate, sort_order

**indian_states**:
- id, state_name, state_code, is_union_territory, is_active

**newsletter_subscriptions**:
- id, email, is_active, subscribed_at

**banks**:
- id, uuid, bank_name, bank_code, logo_url, is_active
- supported_payment_types (JSON), sort_order, created_at, updated_at

**file_storage**:
- id, uuid, file_name, file_path, file_size, mime_type
- file_type, entity_type, entity_id, uploaded_by, is_public
- created_at

**payment_gateways**:
- id, gateway_name, gateway_code, is_active, is_live
- supported_countries (JSON), supported_currencies (JSON)
- config (JSON), sort_order, created_at, updated_at

**user_tax_info**:
- id, user_id, country_id, tax_number, tax_type, business_name
- business_address, is_verified, created_at, updated_at

## Directory Structure

```bash
pavitra-micro/
├── backend/
│ ├── auth/
│ │ ├── main.py
│ │ ├── routes.py
│ │ ├── models.py
│ │ ├── init.py
│ │ ├── requirements.txt
│ │ └── Dockerfile
│ ├── product/
│ │ ├── main.py
│ │ ├── routes.py
│ │ ├── models.py
│ │ ├── init.py
│ │ ├── requirements.txt
│ │ └── Dockerfile
│ ├── order/
│ │ ├── main.py
│ │ ├── routes.py
│ │ ├── models.py
│ │ ├── init.py
│ │ ├── requirements.txt
│ │ └── Dockerfile
│ ├── user/
│ │ ├── main.py
│ │ ├── routes.py
│ │ ├── models.py
│ │ ├── init.py
│ │ ├── requirements.txt
│ │ └── Dockerfile
│ ├── payment/
│ │ ├── main.py
│ │ ├── routes.py
│ │ ├── models.py
│ │ ├── init.py
│ │ ├── requirements.txt
│ │ └── Dockerfile
│ ├── notification/
│ │ ├── main.py
│ │ ├── routes.py
│ │ ├── models.py
│ │ ├── init.py
│ │ ├── requirements.txt
│ │ └── Dockerfile
│ ├── shared/
│ │ ├── config.py
│ │ ├── database.py
│ │ ├── security.py
│ │ ├── logging_config.py
│ │ ├── redis_client.py
│ │ ├── rate_limiter.py
│ │ └── init.py
│ └── init.py
├── frontend/
│ ├── src/
│ │ ├── components/
│ │ ├── pages/
│ │ ├── App.jsx
│ │ ├── main.jsx
│ │ └── index.css
│ ├── package.json
│ ├── vite.config.js
│ ├── index.html
│ └── Dockerfile
├── scripts/
│ ├── 01-database-setup.sql
│ ├── 02_settings.sql
│ ├── 03_roles.sql
│ ├── 04_notifications.sql
│ ├── 05_refunds.sql
│ └── 06_notifications.sql
├── logs/
│ ├── auth.log
│ ├── product.log
│ ├── order.log
│ ├── user.log
│ ├── payment.log
│ └── notification.log
├── .env
├── .env.example
├── docker-compose.yml
├── docker-compose.redis.yml
├── docker-compose.rabbitmq.yml
└── README.md
```


## Environment Configuration
**Essential .env variables**:
- DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
- JWT_SECRET, JWT_ALGORITHM
- SERVICE_PORTS (8001-8006)
- UPLOAD_PATH, CORS_ORIGINS
- REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
- RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASSWORD
- SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD
- RAZORPAY_KEY_ID, RAZORPAY_SECRET
- STRIPE_PUBLISHABLE_KEY, STRIPE_SECRET_KEY

## Deployment Commands
```bash
# Build and start all services
docker-compose up -d --build

# Build specific service
docker-compose build auth-service --no-cache

# View logs
docker-compose logs -f auth-service

# Check service status
docker-compose ps

# Stop services
docker-compose down
```

## Technology Stack
```bash
Backend: Python 3.11, FastAPI, MySQL 8.0, JWT, bcrypt, passlib
Frontend: React 18, React Router, Axios, Vite
Database: MySQL with connection pooling, JSON fields
Security: JWT tokens, bcrypt hashing, input sanitization
Logging: JSON-structured logging with service correlation
Containerization: Docker, Docker Compose
Payments: Razorpay, Stripe integration ready
```

## Current Status
```bash
🟢 PRODUCTION READY - All services implemented, tested, and containerized
🟢 Frontend: Running on http://localhost:3000
🟢 Backend: 6 microservices running on ports 8001-8006
🟢 Database: Complete schema with 30+ tables
🟢 Authentication: JWT with role-based permissions
🟢 Payments: Multi-gateway support
🟢 Notifications: Email/SMS/Push ready
```