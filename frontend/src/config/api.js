// Vite uses import.meta.env for environment variables
const isProduction = import.meta.env.PROD

export const API_CONFIG = {
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
}

export const SERVICE_URLS = {
  AUTH: isProduction ? '/api/v1/auth' : 'http://localhost:8001/api/v1/auth',
  PRODUCTS: isProduction ? '/api/v1/products' : 'http://localhost:8002/api/v1/products',
  ORDERS: isProduction ? '/api/v1/orders' : 'http://localhost:8003/api/v1/orders',
  USERS: isProduction ? '/api/v1/users' : 'http://localhost:8004/api/v1/users',
  PAYMENTS: isProduction ? '/api/v1/payments' : 'http://localhost:8005/api/v1/payments',
  NOTIFICATIONS: isProduction ? '/api/v1/notifications' : 'http://localhost:8006/api/v1/notifications',
}