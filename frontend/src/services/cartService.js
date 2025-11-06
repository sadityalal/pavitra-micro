import { userApi } from './api';
import { sessionManager } from './api';
import { productService } from './productService';

export const cartService = {
  getCart: async () => {
    try {
      console.log('🛒 GET CART - Fetching cart data');
      const response = await userApi.get('/cart');
      console.log('🛒 GET CART - Success:', response.data);

      // Update session if provided
      const sessionId = response.headers['x-session-id'];
      if (sessionId) {
        sessionManager.setSession(sessionId);
      }

      return response.data;
    } catch (error) {
      console.error('🛒 GET CART - Error:', error);
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
      console.log('🛒 ADD_TO_CART: Starting...', { productId, quantity, variationId });

      // Ensure we have a session for guest users
      const token = localStorage.getItem('auth_token');
      if (!token && !sessionManager.getSession()) {
        console.log('🛒 No session found, initializing guest session...');
        try {
          // Initialize session by making a simple API call
          await userApi.get('/health').catch(() => {});
          console.log('✅ Guest session initialized');
        } catch (error) {
          console.log('⚠️ Guest session init failed, continuing anyway...');
        }
      }

      const payload = {
        quantity: parseInt(quantity)
      };

      if (variationId) {
        payload.variation_id = variationId;
      }

      console.log('🛒 Sending request to backend...', payload);
      const response = await userApi.post(`/cart/${productId}`, payload);
      console.log('🛒 Backend response:', response.data);

      // Update session if provided
      const sessionId = response.headers['x-session-id'];
      if (sessionId) {
        sessionManager.setSession(sessionId);
        console.log('✅ Session ID saved:', sessionId);
      }

      return response.data;
    } catch (error) {
      console.error('🛒 ADD_TO_CART ERROR:', error);
      if (error.response?.status === 401) {
        throw new Error('Please log in to add items to cart.');
      } else if (error.response?.status === 404) {
        throw new Error('Product not found.');
      } else if (error.response?.status === 400) {
        throw new Error(error.response.data.detail || 'Cannot add to cart. Please check product availability.');
      } else if (error.response?.status === 422) {
        throw new Error('Invalid quantity or product data.');
      } else if (error.response?.status === 503) {
        throw new Error('Service temporarily unavailable. Please try again later.');
      } else {
        throw new Error('Failed to add to cart. Please try again.');
      }
    }
  },

  updateCartItem: async (cartItemId, quantity) => {
    try {
      console.log('🛒 UPDATE_CART_ITEM:', { cartItemId, quantity });

      if (quantity < 0) {
        throw new Error('Quantity cannot be negative');
      }

      const response = await userApi.put(`/cart/${cartItemId}`, {
        quantity: parseInt(quantity)
      });

      console.log('🛒 Update cart response:', response.data);
      return response.data;
    } catch (error) {
      console.error('🛒 UPDATE_CART_ITEM ERROR:', error);
      if (error.response?.status === 400) {
        throw new Error(error.response.data.detail || 'Cannot update cart item.');
      } else if (error.response?.status === 404) {
        throw new Error('Cart item not found.');
      } else {
        throw new Error('Failed to update cart item. Please try again.');
      }
    }
  },

  removeFromCart: async (cartItemId) => {
    try {
      console.log('🛒 REMOVE_FROM_CART:', cartItemId);
      const response = await userApi.delete(`/cart/${cartItemId}`);
      console.log('🛒 Remove from cart response:', response.data);
      return response.data;
    } catch (error) {
      console.error('🛒 REMOVE_FROM_CART ERROR:', error);
      if (error.response?.status === 404) {
        throw new Error('Cart item not found.');
      } else {
        throw new Error('Failed to remove item from cart. Please try again.');
      }
    }
  },

  clearCart: async () => {
    try {
      console.log('🛒 CLEAR_CART');
      const response = await userApi.delete('/cart');
      console.log('🛒 Clear cart response:', response.data);
      return response.data;
    } catch (error) {
      console.error('🛒 CLEAR_CART ERROR:', error);
      throw new Error('Failed to clear cart. Please try again.');
    }
  },

  migrateGuestCart: async () => {
    try {
      console.log('🛒 MIGRATE_GUEST_CART');
      const response = await userApi.post('/session/cart/migrate-to-user');
      console.log('🛒 Migrate cart response:', response.data);
      return response.data;
    } catch (error) {
      console.error('🛒 MIGRATE_GUEST_CART ERROR:', error);
      throw new Error('Failed to migrate cart. Please try again.');
    }
  },

  // New method to ensure guest session is properly initialized
  ensureGuestSession: async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token && !sessionManager.getSession()) {
        console.log('🛒 Ensuring guest session...');
        // Make a simple API call to initialize session
        await userApi.get('/health');
        console.log('✅ Guest session ensured');
        return true;
      }
      return true;
    } catch (error) {
      console.error('❌ Failed to ensure guest session:', error);
      return false;
    }
  }
};