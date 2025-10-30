const env = {
  development: {
    API_BASE_URL: 'http://localhost:8001',
    ENABLE_DEBUG: true,
    LOG_LEVEL: 'debug'
  },
  production: {
    API_BASE_URL: '',
    ENABLE_DEBUG: false,
    LOG_LEVEL: 'error'
  }
}

export const config = env[import.meta.env.MODE] || env.production