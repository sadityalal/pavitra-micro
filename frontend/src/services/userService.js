import { userApi } from './api';

export const userService = {
  // Get user profile
  getProfile: async () => {
    const response = await userApi.get('/api/v1/users/profile');
    return response.data;
  },

  // Update user profile
  updateProfile: async (profileData) => {
    const response = await userApi.put('/api/v1/users/profile', profileData);
    return response.data;
  },

  // Get user addresses
  getAddresses: async () => {
    const response = await userApi.get('/api/v1/users/addresses');
    return response.data;
  },

  // Add address
  addAddress: async (addressData) => {
    const response = await userApi.post('/api/v1/users/addresses', addressData);
    return response.data;
  },

  // Get wishlist
  getWishlist: async () => {
    const response = await userApi.get('/api/v1/users/wishlist');
    return response.data;
  },

  // Add to wishlist
  addToWishlist: async (productId) => {
    const response = await userApi.post(`/api/v1/users/wishlist/${productId}`);
    return response.data;
  },

  // Remove from wishlist
  removeFromWishlist: async (productId) => {
    const response = await userApi.delete(`/api/v1/users/wishlist/${productId}`);
    return response.data;
  },

  // Admin: Get all users
  getAllUsers: async (skip = 0, limit = 100) => {
    const response = await userApi.get(`/api/v1/users/admin/users?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // Admin: Update user status
  updateUserStatus: async (userId, isActive) => {
    const response = await userApi.put(`/api/v1/users/admin/users/${userId}/status`, {
      is_active: isActive
    });
    return response.data;
  },

  // Check site health
  checkHealth: async () => {
    const response = await userApi.get('/health');
    return response.data;
  }
};
