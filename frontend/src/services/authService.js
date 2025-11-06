import { authApi } from './api';

export const authService = {
  login: async (credentials) => {
    const response = await authApi.post('/login', credentials);
    return response.data;
  },

  register: async (userData) => {
    // Build JSON payload instead of FormData
    const payload = {
      first_name: userData.first_name.trim(),
      last_name: userData.last_name.trim(),
      password: userData.password,
      country_id: userData.country_id || 1
    };

    // Determine auth_type and add the appropriate identifier
    if (userData.email && userData.email.trim()) {
      payload.email = userData.email.trim();
      payload.auth_type = 'email';
    } else if (userData.phone && userData.phone.trim()) {
      payload.phone = userData.phone.trim();
      payload.auth_type = 'mobile';
    } else if (userData.username && userData.username.trim()) {
      payload.username = userData.username.trim();
      payload.auth_type = 'username';
    } else {
      throw new Error('Email, phone, or username is required');
    }

    console.log('Sending registration payload:', payload);
    const response = await authApi.post('/register', payload);
    return response.data;
  },

  logout: async () => {
    const response = await authApi.post('/logout');
    return response.data;
  },

  getFrontendSettings: async () => {
    const response = await authApi.get('/frontend-settings');
    return response.data;
  },

  getSiteSettings: async () => {
    const response = await authApi.get('/site-settings');
    return response.data;
  },

  updateSiteSettings: async (settings) => {
    const response = await authApi.put('/site-settings', settings);
    return response.data;
  },

  refreshToken: async () => {
    const response = await authApi.post('/refresh');
    return response.data;
  },

  checkHealth: async () => {
    const response = await authApi.get('/health');
    return response.data;
  },

  forgotPassword: async (email) => {
    const response = await authApi.post('/forgot-password', { email });
    return response.data;
  },

  resetPassword: async (token, newPassword) => {
    const response = await authApi.post('/reset-password', {
      token,
      new_password: newPassword
    });
    return response.data;
  },

  checkPermission: async (permission) => {
    const response = await authApi.post('/check-permission', { permission });
    return response.data;
  },

  getRoles: async () => {
    const response = await authApi.get('/roles');
    return response.data;
  }
};