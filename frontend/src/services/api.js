import axios from 'axios'

const API_BASE_URL = '/api'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Site Settings API
export const getSiteSettings = async () => {
  try {
    // This would typically come from your backend
    // For now, we'll return mock data that matches your site_settings table
    return {
      site_name: 'Pavitra Trading',
      site_description: 'Your trusted online shopping destination in India',
      currency: 'INR',
      currency_symbol: '₹',
      default_gst_rate: 18.00,
      enable_guest_checkout: true,
      maintenance_mode: false,
      enable_reviews: true,
      enable_wishlist: true,
      min_order_amount: 0.00,
      free_shipping_min_amount: 500.00,
      default_currency: 'INR',
      supported_currencies: ['INR', 'USD', 'GBP', 'EUR'],
      default_country: 'IN',
      app_debug: false,
      log_level: 'INFO',
      cors_origins: ['http://localhost:3000', 'http://localhost:3001'],
      rate_limit_requests: 100,
      rate_limit_window: 900,
      razorpay_test_mode: true,
      stripe_test_mode: true,
      email_notifications: true,
      sms_notifications: true,
      push_notifications: true,
      refund_policy_days: 30,
      auto_refund_enabled: true,
      refund_processing_fee: 0.00
    }
  } catch (error) {
    console.error('Error fetching site settings:', error)
    throw error
  }
}

// Products API
export const getProducts = async (params = {}) => {
  try {
    const response = await api.get('/v1/products', { params })
    return response.data
  } catch (error) {
    console.error('Error fetching products:', error)
    throw error
  }
}

export const getProductBySlug = async (slug) => {
  try {
    const response = await api.get(`/v1/products/${slug}`)
    return response.data
  } catch (error) {
    console.error('Error fetching product:', error)
    throw error
  }
}

export const getFeaturedProducts = async () => {
  try {
    const response = await api.get('/v1/products/featured-products')
    return response.data
  } catch (error) {
    console.error('Error fetching featured products:', error)
    throw error
  }
}

// Auth API
export const loginUser = async (credentials) => {
  try {
    const response = await api.post('/v1/auth/login', credentials)
    return response.data
  } catch (error) {
    console.error('Error logging in:', error)
    throw error
  }
}

export const registerUser = async (userData) => {
  try {
    const response = await api.post('/v1/auth/register', userData)
    return response.data
  } catch (error) {
    console.error('Error registering user:', error)
    throw error
  }
}

// Cart API
export const addToCart = async (productId, quantity = 1) => {
  try {
    const response = await api.post('/v1/cart/add', { productId, quantity })
    return response.data
  } catch (error) {
    console.error('Error adding to cart:', error)
    throw error
  }
}

export default api
