import { userApi } from './api';

export const cartService = {
  getCart: async () => {
    try {
      const response = await userApi.get('/api/v1/users/cart');
      console.log('Cart API Response:', response.data);

      // Ensure the response has the expected structure
      if (response.data && typeof response.data === 'object') {
        return {
          items: response.data.items || [],
          total: response.data.total || 0,
          total_items: response.data.total_items || 0,
          subtotal: response.data.subtotal || 0,
          shipping_cost: response.data.shipping_cost || 0
        };
      }

      return {
        items: [],
        total: 0,
        total_items: 0,
        subtotal: 0,
        shipping_cost: 0
      };
    } catch (error) {
      console.error('Error fetching cart:', error);
      // Return empty cart structure instead of throwing
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

      const payload = {
        quantity: quantity
      };

      if (variationId) {
        payload.variation_id = variationId;
      }

      const response = await userApi.post(`/api/v1/users/cart/${productId}`, payload);
      console.log('Add to cart response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error adding to cart:', error);

      // For development, return mock success if API is down
      if (error.code === 'ERR_NETWORK') {
        console.log('Mocking cart add for development');
        return { success: true, message: 'Item added to cart (mocked)' };
      }

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