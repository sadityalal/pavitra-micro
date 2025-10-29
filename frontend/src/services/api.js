import axios from 'axios'
import { API_CONFIG, SERVICE_URLS } from '../config/api'

// Create axios instances for each service
const createApiInstance = (baseURL) => {
  const instance = axios.create({
    baseURL,
    timeout: API_CONFIG.TIMEOUT,
    headers: {
      'Content-Type': 'application/json',
    },
    withCredentials: true, // Important for CORS with credentials
  })

  // Request interceptor
  instance.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }

      // Add CORS headers for development
      if (process.env.NODE_ENV === 'development') {
        config.headers['Access-Control-Allow-Origin'] = '*'
        config.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        config.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept, Authorization'
      }

      return config
    },
    (error) => Promise.reject(error)
  )

  // Response interceptor
  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config

      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true
        try {
          const refreshToken = localStorage.getItem('refreshToken')
          if (refreshToken) {
            // Implement token refresh logic here
            // const response = await authInstance.post('/refresh', { refresh_token: refreshToken })
            // const newToken = response.data.access_token
            // localStorage.setItem('token', newToken)
            // originalRequest.headers.Authorization = `Bearer ${newToken}`
            // return instance(originalRequest)
          }
        } catch (refreshError) {
          localStorage.removeItem('token')
          localStorage.removeItem('refreshToken')
          localStorage.removeItem('user')
          window.location.href = '/login'
        }
      }

      return Promise.reject(error)
    }
  )

  return instance
}

// Create instances for each service
export const authAPI = createApiInstance(SERVICE_URLS.AUTH)
export const productsAPI = createApiInstance(SERVICE_URLS.PRODUCTS)
export const ordersAPI = createApiInstance(SERVICE_URLS.ORDERS)
export const usersAPI = createApiInstance(SERVICE_URLS.USERS)
export const paymentsAPI = createApiInstance(SERVICE_URLS.PAYMENTS)
export const notificationsAPI = createApiInstance(SERVICE_URLS.NOTIFICATIONS)

// API Methods
export const API = {
  // Auth
  auth: {
    login: (credentials) => authAPI.post('/login', credentials),
    register: (userData) => authAPI.post('/register', userData),
    logout: () => authAPI.post('/logout'),
    refresh: () => authAPI.post('/refresh'),
    forgotPassword: (email) => authAPI.post('/forgot-password', { email }),
    resetPassword: (data) => authAPI.post('/reset-password', data),
    getProfile: () => usersAPI.get('/profile'), // User service for profile
  },

  // Products
  products: {
    getAll: (params = {}) => productsAPI.get('/', { params }),
    getFeatured: () => productsAPI.get('/featured'),
    getBestsellers: () => productsAPI.get('/bestsellers'),
    getNewArrivals: () => productsAPI.get('/new-arrivals'),
    getById: (id) => productsAPI.get(`/${id}`),
    getBySlug: (slug) => productsAPI.get(`/slug/${slug}`),
    getCategories: () => productsAPI.get('/categories/all'),
    getBrands: () => productsAPI.get('/brands/all'),
    search: (query) => productsAPI.get('/', { params: { search: query } }),
  },

  // Users
  users: {
    getProfile: () => usersAPI.get('/profile'),
    updateProfile: (data) => usersAPI.put('/profile', data),
    getAddresses: () => usersAPI.get('/addresses'),
    addAddress: (data) => usersAPI.post('/addresses', data),
    updateAddress: (id, data) => usersAPI.put(`/addresses/${id}`, data),
    deleteAddress: (id) => usersAPI.delete(`/addresses/${id}`),
    getWishlist: () => usersAPI.get('/wishlist'),
    addToWishlist: (productId) => usersAPI.post(`/wishlist/${productId}`),
    removeFromWishlist: (productId) => usersAPI.delete(`/wishlist/${productId}`),
    getCart: () => usersAPI.get('/cart'),
    addToCart: (productId, quantity = 1) => usersAPI.post(`/cart/${productId}`, { quantity }),
    updateCartItem: (cartItemId, quantity) => usersAPI.put(`/cart/${cartItemId}`, { quantity }),
    removeFromCart: (cartItemId) => usersAPI.delete(`/cart/${cartItemId}`),
    clearCart: () => usersAPI.delete('/cart'),
  },

  // Orders
  orders: {
    create: (data) => ordersAPI.post('/', data),
    getById: (id) => ordersAPI.get(`/${id}`),
    getUserOrders: (params = {}) => ordersAPI.get('/user/current', { params }),
    updateStatus: (id, data) => ordersAPI.put(`/${id}/status`, data),
    cancel: (id, reason) => ordersAPI.post(`/${id}/cancel`, { reason }),
  },

  // Payments
  payments: {
    initiate: (data) => paymentsAPI.post('/initiate', data),
    verify: (paymentId, data) => paymentsAPI.post(`/verify/${paymentId}`, data),
    getMethods: () => paymentsAPI.get('/methods'),
    savePaymentMethod: (data) => paymentsAPI.post('/save-payment-method', data),
    getTransactions: () => paymentsAPI.get('/transactions'),
    createRefund: (data) => paymentsAPI.post('/refund', data),
  },

  // Notifications
  notifications: {
    getPreferences: () => usersAPI.get('/notification-preferences'),
    updatePreferences: (data) => usersAPI.put('/notification-preferences', data),
  },
}

export default API