// API service for backend communication
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000'\;

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, config);
      
      // Handle non-JSON responses
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(data.detail || `HTTP ${response.status}: ${response.statusText}`);
        }
        return data;
      } else {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.text();
      }
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Auth endpoints
  async login(loginData) {
    return this.request('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(loginData)
    });
  }

  async register(userData) {
    const formData = new FormData();
    Object.keys(userData).forEach(key => {
      if (userData[key] !== null && userData[key] !== undefined) {
        formData.append(key, userData[key]);
      }
    });

    return fetch(`${this.baseURL}/api/v1/auth/register`, {
      method: 'POST',
      body: formData,
    });
  }

  async logout() {
    return this.request('/api/v1/auth/logout', {
      method: 'POST'
    });
  }

  async refreshToken() {
    return this.request('/api/v1/auth/refresh', {
      method: 'POST'
    });
  }

  async getSiteSettings() {
    return this.request('/api/v1/auth/site-settings');
  }

  // Product endpoints
  async getProducts(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/api/v1/products?${queryString}`);
  }

  async getProduct(slugOrId) {
    return this.request(`/api/v1/products/${slugOrId}`);
  }

  async getCategories() {
    return this.request('/api/v1/products/categories');
  }

  async getBrands() {
    return this.request('/api/v1/products/brands');
  }

  // User endpoints
  async getUserProfile() {
    return this.request('/api/v1/users/profile');
  }

  async updateUserProfile(profileData) {
    return this.request('/api/v1/users/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData)
    });
  }

  async getUserAddresses() {
    return this.request('/api/v1/users/addresses');
  }

  async addAddress(addressData) {
    return this.request('/api/v1/users/addresses', {
      method: 'POST',
      body: JSON.stringify(addressData)
    });
  }

  async updateAddress(addressId, addressData) {
    return this.request(`/api/v1/users/addresses/${addressId}`, {
      method: 'PUT',
      body: JSON.stringify(addressData)
    });
  }

  async deleteAddress(addressId) {
    return this.request(`/api/v1/users/addresses/${addressId}`, {
      method: 'DELETE'
    });
  }

  // Cart endpoints
  async getCart() {
    return this.request('/api/v1/users/cart');
  }

  async addToCart(productId, quantity = 1) {
    return this.request(`/api/v1/users/cart/${productId}?quantity=${quantity}`, {
      method: 'POST'
    });
  }

  async updateCartItem(cartItemId, quantity) {
    return this.request(`/api/v1/users/cart/${cartItemId}?quantity=${quantity}`, {
      method: 'PUT'
    });
  }

  async removeFromCart(cartItemId) {
    return this.request(`/api/v1/users/cart/${cartItemId}`, {
      method: 'DELETE'
    });
  }

  async clearCart() {
    return this.request('/api/v1/users/cart', {
      method: 'DELETE'
    });
  }

  // Wishlist endpoints
  async getWishlist() {
    return this.request('/api/v1/users/wishlist');
  }

  async addToWishlist(productId) {
    return this.request(`/api/v1/users/wishlist/${productId}`, {
      method: 'POST'
    });
  }

  async removeFromWishlist(productId) {
    return this.request(`/api/v1/users/wishlist/${productId}`, {
      method: 'DELETE'
    });
  }
}

export default new ApiService();
