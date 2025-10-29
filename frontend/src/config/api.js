// API Configuration
export const API_CONFIG = {
  BASE_URL: process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8000',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
}

// Service URLs for development
export const SERVICE_URLS = {
  AUTH: process.env.NODE_ENV === 'production' ? '/api/v1/auth' : 'http://localhost:8001/api/v1/auth',
  PRODUCTS: process.env.NODE_ENV === 'production' ? '/api/v1/products' : 'http://localhost:8002/api/v1/products',
  ORDERS: process.env.NODE_ENV === 'production' ? '/api/v1/orders' : 'http://localhost:8003/api/v1/orders',
  USERS: process.env.NODE_ENV === 'production' ? '/api/v1/users' : 'http://localhost:8004/api/v1/users',
  PAYMENTS: process.env.NODE_ENV === 'production' ? '/api/v1/payments' : 'http://localhost:8005/api/v1/payments',
  NOTIFICATIONS: process.env.NODE_ENV === 'production' ? '/api/v1/notifications' : 'http://localhost:8006/api/v1/notifications',
}