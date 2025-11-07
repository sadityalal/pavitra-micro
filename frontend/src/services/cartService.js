import { userApi } from './api';
import { sessionManager } from './api';

export const cartService = {
  getCart: async () => {
  try {
    const currentSession = sessionManager.getSession();
    const token = localStorage.getItem('auth_token');

    console.log('🛒 GET CART - Session:', currentSession, 'Token:', !!token);

    const response = await userApi.get('/cart');
    console.log('🛒 GET CART - Response:', response.data);

    // Also try the debug endpoint
    try {
      const debugResponse = await userApi.get('/cart/debug');
      console.log('🛒 DEBUG CART - Response:', debugResponse.data);
    } catch (debugError) {
      console.log('🛒 DEBUG endpoint failed:', debugError);
    }

    return response.data;
  } catch (error) {
    console.error('🛒 GET CART - Error:', error);
    console.error('🛒 Error response:', error.response?.data);
    return {
      items: [],
      subtotal: 0,
      total_items: 0
    };
  }
},

  addToCart: async (productId, quantity = 1, variationId = null) => {
    try {
      const currentSession = sessionManager.getSession();
      console.log('🛒 ADD_TO_CART: Current session:', currentSession);

      // Ensure we have a session before making the request
      if (!currentSession) {
        console.log('🛒 No session found, ensuring session...');
        await cartService.ensureGuestSession();
      }

      const payload = {
        quantity: parseInt(quantity)
      };

      if (variationId) {
        payload.variation_id = variationId;
      }

      console.log('🛒 Sending request with session:', sessionManager.getSession());
      const response = await userApi.post(`/cart/${productId}`, payload);
      console.log('🛒 Backend response:', response.data);

      // Update session from response headers
      const sessionId = response.headers['x-session-id'] || response.headers['x-secure-session-id'];
      if (sessionId) {
        sessionManager.setSession(sessionId);
        console.log('✅ Session ID saved from addToCart:', sessionId);
      } else {
        console.warn('⚠️ No session ID in addToCart response headers');
      }

      return response.data;
    } catch (error) {
      console.error('🛒 ADD_TO_CART ERROR:', error);
      console.error('🛒 Error response:', error.response?.data);
      console.error('🛒 Error status:', error.response?.status);

      if (error.response?.status === 401) {
        throw new Error('Please log in to add items to cart.');
      } else if (error.response?.status === 404) {
        throw new Error('Product not found.');
      } else if (error.response?.status === 400) {
        throw new Error(error.response.data.detail || 'Cannot add to cart. Please check product availability.');
      } else if (error.response?.status === 500) {
        throw new Error('Server error. Please try again.');
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

  ensureGuestSession: async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token && !sessionManager.getSession()) {
        console.log('🛒 Ensuring guest session...');
        const response = await fetch('/api/v1/users/health', {
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        const sessionId = response.headers.get('x-session-id') ||
                         response.headers.get('x-secure-session-id');
        if (sessionId) {
          sessionManager.setSession(sessionId);
          console.log('✅ Guest session ensured:', sessionId);
          return true;
        }
      }
      return true;
    } catch (error) {
      console.error('❌ Failed to ensure guest session:', error);
      return false;
    }
  }
};