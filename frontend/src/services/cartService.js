import { userApi } from './api';

export const cartService = {
  getCart: async () => {
    try {
      const response = await userApi.get('/api/v1/users/cart');
      console.log('Cart response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error fetching cart:', error);
      // Return empty cart structure on error
      return {
        items: [],
        subtotal: 0,
        total_items: 0
      };
    }
  },

  addToCart: async (productId, quantity = 1, variationId = null) => {
    try {
      console.log('Adding to cart - product:', productId, 'qty:', quantity);

      const payload = {
        quantity: parseInt(quantity)
      };

      if (variationId) {
        payload.variation_id = variationId;
      }

      const response = await userApi.post(`/api/v1/users/cart/${productId}`, payload);
      console.log('Add to cart success:', response.data);
      return response.data;
    } catch (error) {
      console.error('Add to cart error:', error);
      throw error;
    }
  },

  updateCartItem: async (cartItemId, quantity) => {
    try {
      const response = await userApi.put(`/api/v1/users/cart/${cartItemId}`, {
        quantity: parseInt(quantity)
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