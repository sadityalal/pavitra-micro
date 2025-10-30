import { config } from './environment.js'

const isProduction = import.meta.env.PROD

export const SERVICE_URLS = {
  AUTH: isProduction ? '/api/v1/auth' : `${config.AUTH_SERVICE_URL}/api/v1/auth`,
  PRODUCTS: isProduction ? '/api/v1/products' : `${config.PRODUCT_SERVICE_URL}/api/v1/products`,
  USERS: isProduction ? '/api/v1/users' : `${config.USER_SERVICE_URL}/api/v1/users`,
  ORDERS: isProduction ? '/api/v1/orders' : `${config.ORDER_SERVICE_URL}/api/v1/orders`,
  PAYMENTS: isProduction ? '/api/v1/payments' : `${config.PAYMENT_SERVICE_URL}/api/v1/payments`,
}

export const getImageUrl = (imagePath) => {
  if (!imagePath) {
    return '/images/placeholder-product.jpg'
  }

  // If it's already a full URL, return as is
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
    return imagePath
  }

  // For ALL environments, use the full backend URL
  // This is the key fix - always go directly to the backend for images
  const backendUrl = config.PRODUCT_SERVICE_URL
  const normalizedPath = imagePath.startsWith('/') ? imagePath : `/${imagePath}`
  return `${backendUrl}${normalizedPath}`
}

export const API_CONFIG = {
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
}