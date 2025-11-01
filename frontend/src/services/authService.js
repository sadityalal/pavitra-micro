import { authApi } from './api';

export const authService = {
  login: async (credentials) => {
    const response = await authApi.post('/api/v1/auth/login', credentials);
    return response.data;
  },

  register: async (userData) => {
    // Transform data to match backend expectations
    const registerPayload = {
      first_name: userData.first_name,
      last_name: userData.last_name,
      email: userData.email,
      phone: userData.phone || null,
      username: userData.username || null,
      password: userData.password,
      country_id: userData.country_id || 1,
      auth_type: userData.email ? 'email' : 'mobile'
    };

    const response = await authApi.post('/api/v1/auth/register', registerPayload);
    return response.data;
  },

  logout: async () => {
    const response = await authApi.post('/api/v1/auth/logout');
    return response.data;
  },

  getFrontendSettings: async () => {
    const response = await authApi.get('/api/v1/auth/frontend-settings');
    return response.data;
  },

  getSiteSettings: async () => {
    const response = await authApi.get('/api/v1/auth/site-settings');
    return response.data;
  },

  updateSiteSettings: async (settings) => {
    const response = await authApi.put('/api/v1/auth/site-settings', settings);
    return response.data;
  },

  refreshToken: async () => {
    const response = await authApi.post('/api/v1/auth/refresh');
    return response.data;
  },

  checkHealth: async () => {
    const response = await authApi.get('/health');
    return response.data;
  },

  forgotPassword: async (email) => {
    const response = await authApi.post('/api/v1/auth/forgot-password', { email });
    return response.data;
  },

  resetPassword: async (token, newPassword) => {
    const response = await authApi.post('/api/v1/auth/reset-password', {
      token,
      new_password: newPassword
    });
    return response.data;
  },

  checkPermission: async (permission) => {
    const response = await authApi.post('/api/v1/auth/check-permission', { permission });
    return response.data;
  },

  getRoles: async () => {
    const response = await authApi.get('/api/v1/auth/roles');
    return response.data;
  }
};