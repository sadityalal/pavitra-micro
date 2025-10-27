import { apiService } from './api';

class UserService {
  async getProfile() {
    try {
      return await apiService.get('/api/v1/users/profile');
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
      throw error;
    }
  }

  async updateProfile(profileData) {
    try {
      return await apiService.put('/api/v1/users/profile', profileData);
    } catch (error) {
      console.error('Failed to update profile:', error);
      throw error;
    }
  }

  async getAddresses() {
    try {
      return await apiService.get('/api/v1/users/addresses');
    } catch (error) {
      console.error('Failed to fetch addresses:', error);
      return [];
    }
  }

  async addAddress(addressData) {
    try {
      return await apiService.post('/api/v1/users/addresses', addressData);
    } catch (error) {
      console.error('Failed to add address:', error);
      throw error;
    }
  }

  async updateAddress(addressId, addressData) {
    try {
      return await apiService.put(`/api/v1/users/addresses/${addressId}`, addressData);
    } catch (error) {
      console.error('Failed to update address:', error);
      throw error;
    }
  }

  async deleteAddress(addressId) {
    try {
      return await apiService.delete(`/api/v1/users/addresses/${addressId}`);
    } catch (error) {
      console.error('Failed to delete address:', error);
      throw error;
    }
  }

  async getWishlist() {
    try {
      return await apiService.get('/api/v1/users/wishlist');
    } catch (error) {
      console.error('Failed to fetch wishlist:', error);
      return { items: [], total_count: 0 };
    }
  }

  async addToWishlist(productId) {
    try {
      return await apiService.post(`/api/v1/users/wishlist/${productId}`);
    } catch (error) {
      console.error('Failed to add to wishlist:', error);
      throw error;
    }
  }

  async removeFromWishlist(productId) {
    try {
      return await apiService.delete(`/api/v1/users/wishlist/${productId}`);
    } catch (error) {
      console.error('Failed to remove from wishlist:', error);
      throw error;
    }
  }

  async getCart() {
    try {
      return await apiService.get('/api/v1/users/cart');
    } catch (error) {
      console.error('Failed to fetch cart:', error);
      return { items: [], subtotal: 0, total_items: 0 };
    }
  }

  async addToCart(productId, quantity = 1) {
    try {
      const formData = new FormData();
      formData.append('quantity', quantity);
      
      return await apiService.postFormData(`/api/v1/users/cart/${productId}`, formData);
    } catch (error) {
      console.error('Failed to add to cart:', error);
      throw error;
    }
  }

  async updateCartItem(cartItemId, quantity) {
    try {
      const formData = new FormData();
      formData.append('quantity', quantity);
      
      return await apiService.postFormData(`/api/v1/users/cart/${cartItemId}`, formData);
    } catch (error) {
      console.error('Failed to update cart item:', error);
      throw error;
    }
  }

  async removeFromCart(cartItemId) {
    try {
      return await apiService.delete(`/api/v1/users/cart/${cartItemId}`);
    } catch (error) {
      console.error('Failed to remove from cart:', error);
      throw error;
    }
  }

  async clearCart() {
    try {
      return await apiService.delete('/api/v1/users/cart');
    } catch (error) {
      console.error('Failed to clear cart:', error);
      throw error;
    }
  }

  async getNotificationPreferences() {
    try {
      return await apiService.get('/api/v1/users/notification-preferences');
    } catch (error) {
      console.error('Failed to fetch notification preferences:', error);
      return { notification_methods: [] };
    }
  }

  async updateNotificationPreferences(preferences) {
    try {
      return await apiService.put('/api/v1/users/notification-preferences', preferences);
    } catch (error) {
      console.error('Failed to update notification preferences:', error);
      throw error;
    }
  }
}

export const userService = new UserService();
