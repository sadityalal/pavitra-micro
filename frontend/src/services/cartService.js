import { userApi } from './api';

export const cartService = {
  getCart: async () => {
    try {
      const response = await userApi.get('/api/v1/users/cart');
      console.log('Cart API Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error fetching cart:', error);
      // Return empty cart structure
      return {
        items: [],
        total: 0,
        total_items: 0,
        subtotal: 0,
        shipping_cost: 0
      };
    }
  },

  addToCart: async (productId, quantity = 1, variationId = null) => {
    try {
      console.log('Adding to cart:', { productId, quantity, variationId });
      const response = await userApi.post(`/api/v1/users/cart/${productId}`, {
        quantity,
        variation_id: variationId
      });
      console.log('Add to cart response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error adding to cart:', error);
      throw error;
    }
  },

  updateCartItem: async (cartItemId, quantity) => {
    try {
      const response = await userApi.put(`/api/v1/users/cart/${cartItemId}`, {
        quantity
      });
      return response.data;
    } catch (error) {
      console.error('Error updating cart:', error);
      throw error;
    }
  },

  removeFromCart: async (cartItemId) => {
    try {
      const response = await userApi.delete(`/api/v1/users/cart/${cartItemId}`);
      return response.data;
    } catch (error) {
      console.error('Error removing from cart:', error);
      throw error;
    }
  },

  clearCart: async () => {
    try {
      const response = await userApi.delete('/api/v1/users/cart');
      return response.data;
    } catch (error) {
      console.error('Error clearing cart:', error);
      throw error;
    }
  }
};