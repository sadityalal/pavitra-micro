import { authApi } from './api';

export const authService = {
  // Login user
  login: async (credentials) => {
    const response = await authApi.post('/api/v1/auth/login', credentials);
    return response.data;
  },

  // Register user
  register: async (userData) => {
    const response = await authApi.post('/api/v1/auth/register', userData);
    return response.data;
  },

  // Logout user
  logout: async () => {
    const response = await authApi.post('/api/v1/auth/logout');
    return response.data;
  },

  // Get frontend settings (public endpoint - no auth required)
  getFrontendSettings: async () => {
    const response = await authApi.get('/api/v1/auth/frontend-settings');
    return response.data;
  },

  // Get site settings (admin only - requires auth)
  getSiteSettings: async () => {
    const response = await authApi.get('/api/v1/auth/site-settings');
    return response.data;
  },

  // Update site settings (admin only)
  updateSiteSettings: async (settings) => {
    const response = await authApi.put('/api/v1/auth/site-settings', settings);
    return response.data;
  },

  // Refresh token
  refreshToken: async () => {
    const response = await authApi.post('/api/v1/auth/refresh');
    return response.data;
  },

  // Check site health
  checkHealth: async () => {
    const response = await authApi.get('/health');
    return response.data;
  },

  // Forgot password
  forgotPassword: async (email) => {
    const response = await authApi.post('/api/v1/auth/forgot-password', { email });
    return response.data;
  },

  // Reset password
  resetPassword: async (token, newPassword) => {
    const response = await authApi.post('/api/v1/auth/reset-password', {
      token,
      new_password: newPassword
    });
    return response.data;
  },

  // Check user permissions
  checkPermission: async (permission) => {
    const response = await authApi.post('/api/v1/auth/check-permission', { permission });
    return response.data;
  },

  // Get all roles
  getRoles: async () => {
    const response = await authApi.get('/api/v1/auth/roles');
    return response.data;
  }
};
