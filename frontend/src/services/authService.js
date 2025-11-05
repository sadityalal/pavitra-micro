import { authApi } from './api';

export const authService = {
  login: async (credentials) => {
    const response = await authApi.post('/login', credentials);
    return response.data;
  },

  register: async (userData) => {
    const formData = new FormData();
    formData.append('first_name', userData.first_name.trim());
    formData.append('last_name', userData.last_name.trim());
    formData.append('password', userData.password);
    formData.append('country_id', userData.country_id || 1);

    if (userData.email && userData.email.trim()) {
      formData.append('email', userData.email.trim());
    }
    if (userData.phone && userData.phone.trim()) {
      formData.append('phone', userData.phone.trim());
    }
    if (userData.username && userData.username.trim()) {
      formData.append('username', userData.username.trim());
    }

    console.log('Sending registration form data:', Object.fromEntries(formData));
    const response = await authApi.post('/register', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
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