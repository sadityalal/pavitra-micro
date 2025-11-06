import { userApi } from './api';

export const cartService = {
  getCart: async () => {
    try {
      console.log('🛒 GET CART - Fetching cart data');
      const response = await userApi.get('/cart');
      console.log('🛒 GET CART - Success:', response.data);
      return response.data;
    } catch (error) {
      console.error('🛒 GET CART - Error:', error);
      return {
        items: [],
        subtotal: 0,
        total_items: 0
      };
    }
  },

  addToCart: async (productId, quantity = 1, variationId = null) => {
  try {
    console.log('🛒 ADD_TO_CART: Starting...', { productId, quantity, variationId });

    // Session check karo
    if (!sessionManager.getSession()) {
      console.log('🛒 No session, initializing...');
      try {
        await productService.getFeaturedProducts();
        console.log('✅ Session initialized');
      } catch (error) {
        console.log('⚠️ Session init failed, continuing anyway...');
      }
    }

    const payload = {
      quantity: parseInt(quantity)
    };
    if (variationId) {
      payload.variation_id = variationId;
    }

    console.log('🛒 Sending request to backend...');
    const response = await userApi.post(`/cart/${productId}`, payload);
    console.log('🛒 Backend response:', response.data);

    // Naya session ID agar aaya to save karo
    const sessionId = response.headers['x-session-id'];
    if (sessionId) {
      sessionManager.setSession(sessionId);
      console.log('✅ Session ID saved:', sessionId);
    }

    return response.data;

  } catch (error) {
    console.error('🛒 ADD_TO_CART ERROR:', error);

    if (error.response?.status === 401) {
      throw new Error('Session issue. Please refresh the page.');
    } else if (error.response?.status === 404) {
      throw new Error('Product not found.');
    } else if (error.response?.status === 400) {
      throw new Error(error.response.data.detail || 'Cannot add to cart.');
    } else {
      throw new Error('Failed to add to cart. Please try again.');
    }
  }
},

  updateCartItem: async (cartItemId, quantity) => {
    try {
      const response = await userApi.put(`/cart/${cartItemId}`, {
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
      const response = await userApi.delete(`/cart/${cartItemId}`);
      return response.data;
    } catch (error) {
      console.error('Error removing from cart:', error);
      throw error;
    }
  },

  clearCart: async () => {
    try {
      const response = await userApi.delete('/cart');
      return response.data;
    } catch (error) {
      console.error('Error clearing cart:', error);
      throw error;
    }
  }
};