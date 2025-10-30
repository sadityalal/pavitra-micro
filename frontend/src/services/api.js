import axios from 'axios'
import { API_CONFIG, SERVICE_URLS } from '../config/api'

const createApiInstance = (baseURL) => {
  const instance = axios.create({
    baseURL,
    timeout: API_CONFIG.TIMEOUT,
    headers: {
      'Content-Type': 'application/json',
    },
    withCredentials: true,
  })

  instance.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      // Add cache busting for GET requests
      if (config.method === 'get') {
        config.params = {
          ...config.params,
          _t: Date.now()
        }
      }
      return config
    },
    (error) => Promise.reject(error)
  )

  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config
      
      // Retry logic for server errors
      if (!originalRequest._retryCount) {
        originalRequest._retryCount = 0
      }
      
      if (originalRequest._retryCount < API_CONFIG.RETRY_ATTEMPTS &&
          (!error.response || error.response.status >= 500)) {
        originalRequest._retryCount++
        const delay = Math.pow(2, originalRequest._retryCount) * 1000
        await new Promise(resolve => setTimeout(resolve, delay))
        return instance(originalRequest)
      }

      // Handle 401 errors (token refresh)
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true
        try {
          const refreshResponse = await authAPI.refresh()
          const { access_token } = refreshResponse.data
          if (access_token) {
            localStorage.setItem('token', access_token)
            originalRequest.headers.Authorization = `Bearer ${access_token}`
            return instance(originalRequest)
          }
        } catch (refreshError) {
          localStorage.removeItem('token')
          window.location.href = '/login'
        }
      }
      
      return Promise.reject(error)
    }
  )

  return instance
}

export const authAPI = createApiInstance(SERVICE_URLS.AUTH)
export const productsAPI = createApiInstance(SERVICE_URLS.PRODUCTS)
export const ordersAPI = createApiInstance(SERVICE_URLS.ORDERS)
export const usersAPI = createApiInstance(SERVICE_URLS.USERS)
export const paymentsAPI = createApiInstance(SERVICE_URLS.PAYMENTS)
export const notificationsAPI = createApiInstance(SERVICE_URLS.NOTIFICATIONS)

export const API = {
  auth: {
    login: (credentials) => authAPI.post('/login', credentials),
    register: (userData) => authAPI.post('/register', userData),
    logout: () => authAPI.post('/logout'),
    refresh: () => authAPI.post('/refresh'),
    forgotPassword: (email) => authAPI.post('/forgot-password', { email }),
    resetPassword: (data) => authAPI.post('/reset-password', data),
    getProfile: () => authAPI.get('/profile'),
  },
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
    addToCart: (productId, quantity = 1, variationId = null) =>
      usersAPI.post(`/cart/${productId}`, { quantity, variation_id: variationId }),
    updateCartItem: (cartItemId, quantity) => usersAPI.put(`/cart/${cartItemId}`, { quantity }),
    removeFromCart: (cartItemId) => usersAPI.delete(`/cart/${cartItemId}`),
    clearCart: () => usersAPI.delete('/cart'),
  },
  orders: {
    create: (data) => ordersAPI.post('/', data),
    getById: (id) => ordersAPI.get(`/${id}`),
    getUserOrders: (params = {}) => ordersAPI.get('/user/current', { params }),
    updateStatus: (id, data) => ordersAPI.put(`/${id}/status`, data),
    cancel: (id, reason) => ordersAPI.post(`/${id}/cancel`, { reason }),
  },
  payments: {
    initiate: (data) => paymentsAPI.post('/initiate', data),
    verify: (paymentId, data) => paymentsAPI.post(`/verify/${paymentId}`, data),
    getMethods: () => paymentsAPI.get('/methods'),
    savePaymentMethod: (data) => paymentsAPI.post('/save-payment-method', data),
    getTransactions: () => paymentsAPI.get('/transactions'),
    createRefund: (data) => paymentsAPI.post('/refund', data),
  },
}

export default API
