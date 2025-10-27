import { apiService } from './api';

class AuthService {
  async login(loginData) {
    try {
      const response = await apiService.post('/api/v1/auth/login', loginData);
      
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
      throw error;
    }
  }

  async register(userData) {
    try {
      // Convert to FormData for registration endpoint
      const formData = new FormData();
      Object.keys(userData).forEach(key => {
        if (userData[key] !== null && userData[key] !== undefined) {
          formData.append(key, userData[key]);
        }
      });

      const response = await apiService.postFormData('/api/v1/auth/register', formData);
      
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
      throw error;
    }
  }

  async logout() {
    try {
      await apiService.post('/api/v1/auth/logout');
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_data');
    }
  }

  async refreshToken() {
    try {
      const response = await apiService.post('/api/v1/auth/refresh');
      
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
      return await apiService.get('/api/v1/auth/site-settings');
    } catch (error) {
      console.error('Failed to fetch site settings:', error);
      // Return default settings if API fails
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
    return !!localStorage.getItem('auth_token');
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
