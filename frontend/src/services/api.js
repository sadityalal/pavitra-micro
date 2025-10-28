// frontend/src/services/api.js
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

class ApiService {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL;
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

    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, config);

      let data;
      try {
        data = await response.json();
      } catch (e) {
        data = { message: 'Invalid response from server' };
      }

      if (!response.ok) {
        throw new Error(data.detail || data.message || `HTTP error! status: ${response.status}`);
      }

      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  async get(endpoint) {
    return this.request(endpoint);
  }

  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete(endpoint) {
    return this.request(endpoint, {
      method: 'DELETE',
    });
  }

  async postFormData(endpoint, formData) {
    const url = `${this.baseURL}${endpoint}`;
    const token = localStorage.getItem('auth_token');

    const config = {
      method: 'POST',
      headers: {
        Authorization: token ? `Bearer ${token}` : '',
      },
      body: formData,
    };

    try {
      const response = await fetch(url, config);

      let data;
      try {
        data = await response.json();
      } catch (e) {
        data = { message: 'Invalid response from server' };
      }

      if (!response.ok) {
        throw new Error(data.detail || data.message || `HTTP error! status: ${response.status}`);
      }

      return data;
    } catch (error) {
      console.error('Form data request failed:', error);
      throw error;
    }
  }
}

// Create service instances for different backend services with different names
export const authApi = new ApiService('http://localhost:8001');
export const productApi = new ApiService('http://localhost:8002');
export const userApi = new ApiService('http://localhost:8004');
export const apiService = new ApiService(); // Default instance