const env = {
  development: {
    AUTH_SERVICE_URL: 'http://localhost:8001',
    PRODUCT_SERVICE_URL: 'http://localhost:8002',  // This is critical
    ORDER_SERVICE_URL: 'http://localhost:8003',
    USER_SERVICE_URL: 'http://localhost:8004',
    PAYMENT_SERVICE_URL: 'http://localhost:8005',
    ENABLE_DEBUG: true,
    LOG_LEVEL: 'debug'
  },
  production: {
    AUTH_SERVICE_URL: 'http://localhost:8001',
    PRODUCT_SERVICE_URL: 'http://localhost:8002',  // This is critical
    ORDER_SERVICE_URL: 'http://localhost:8003',
    USER_SERVICE_URL: 'http://localhost:8004',
    PAYMENT_SERVICE_URL: 'http://localhost:8005',
    ENABLE_DEBUG: true,
    LOG_LEVEL: 'debug'
  }
}

export const config = env[import.meta.env.MODE] || env.production