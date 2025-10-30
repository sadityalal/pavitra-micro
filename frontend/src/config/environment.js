const env = {
  development: {
    AUTH_SERVICE_URL: 'http://localhost:8001',
    PRODUCT_SERVICE_URL: 'http://localhost:8002',
    ORDER_SERVICE_URL: 'http://localhost:8003',
    USER_SERVICE_URL: 'http://localhost:8004',
    PAYMENT_SERVICE_URL: 'http://localhost:8005',
    ENABLE_DEBUG: true,
    LOG_LEVEL: 'debug'
  },
  production: {
    AUTH_SERVICE_URL: '',
    PRODUCT_SERVICE_URL: '',
    ORDER_SERVICE_URL: '',
    USER_SERVICE_URL: '',
    PAYMENT_SERVICE_URL: '',
    ENABLE_DEBUG: false,
    LOG_LEVEL: 'error'
  }
}

export const config = env[import.meta.env.MODE] || env.production