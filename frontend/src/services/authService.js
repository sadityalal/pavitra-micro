// frontend/src/services/authService.js
import { authApi } from './api';

class AuthService {
  async login(loginData) {
    try {
      const response = await authApi.post('/api/v1/auth/login', loginData);

      if (response.access_token) {
        localStorage.setItem('auth_token', response.access_token);
        localStorage.setItem('user_data', JSON.stringify({
          roles: response.user_roles,
          permissions: response.user_permissions
        }));
      }

      return response;
    } catch (error) {
      console.error('Login failed:', error);
      throw new Error(error.message || 'Login failed. Please check your credentials.');
    }
  }

  async register(userData) {
    try {
      // Convert to FormData for multipart/form-data as required by your backend
      const formData = new FormData();

      Object.keys(userData).forEach(key => {
        if (userData[key] !== null && userData[key] !== undefined) {
          formData.append(key, userData[key]);
        }
      });

      const response = await authApi.postFormData('/api/v1/auth/register', formData);

      if (response.access_token) {
        localStorage.setItem('auth_token', response.access_token);
        localStorage.setItem('user_data', JSON.stringify({
          roles: response.user_roles,
          permissions: response.user_permissions
        }));
      }

      return response;
    } catch (error) {
      console.error('Registration failed:', error);
      throw new Error(error.message || 'Registration failed. Please try again.');
    }
  }

  async logout() {
    try {
      await authApi.post('/api/v1/auth/logout');
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_data');
    }
  }

  async refreshToken() {
    try {
      const response = await authApi.post('/api/v1/auth/refresh');
      if (response.access_token) {
        localStorage.setItem('auth_token', response.access_token);
      }
      return response;
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.logout();
      throw error;
    }
  }

  async getSiteSettings() {
    try {
      return await authApi.get('/api/v1/auth/site-settings');
    } catch (error) {
      console.error('Failed to fetch site settings:', error);
      return {
        site_name: 'Pavitra Enterprises',
        currency_symbol: '₹',
        free_shipping_threshold: 999,
        return_period_days: 10,
        site_phone: '+91-9711317009',
        site_email: 'support@pavitraenterprises.com'
      };
    }
  }

  isAuthenticated() {
    const token = localStorage.getItem('auth_token');
    return !!token;
  }

  getToken() {
    return localStorage.getItem('auth_token');
  }

  getUserData() {
    const userData = localStorage.getItem('user_data');
    return userData ? JSON.parse(userData) : null;
  }
}

export const authService = new AuthService();