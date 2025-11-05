import { userApi } from './api';

export const userService = {
  getProfile: async () => {
    const response = await userApi.get('/profile');
    return response.data;
  },

  updateProfile: async (profileData) => {
    const response = await userApi.put('/profile', profileData);
    return response.data;
  },

  getAddresses: async () => {
    const response = await userApi.get('/addresses');
    return response.data;
  },

  addAddress: async (addressData) => {
    const response = await userApi.post('/addresses', addressData);
    return response.data;
  },

  getWishlist: async () => {
    const response = await userApi.get('/wishlist');
    return response.data;
  },

  addToWishlist: async (productId) => {
    const response = await userApi.post(`/wishlist/${productId}`);
    return response.data;
  },

  removeFromWishlist: async (productId) => {
    const response = await userApi.delete(`/wishlist/${productId}`);
    return response.data;
  },

  getAllUsers: async (skip = 0, limit = 100) => {
    const response = await userApi.get(`/admin/users?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  updateUserStatus: async (userId, isActive) => {
    const response = await userApi.put(`/admin/users/${userId}/status`, {
      is_active: isActive
    });
    return response.data;
  },

  checkHealth: async () => {
    const response = await userApi.get('/health');
    return response.data;
  }
};