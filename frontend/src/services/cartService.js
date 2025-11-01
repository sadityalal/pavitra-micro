import { userApi } from './api';

export const cartService = {
  // Get cart items
  getCart: async () => {
    const response = await userApi.get('/api/v1/users/cart');
    return response.data;
  },

  // Add to cart
  addToCart: async (productId, quantity = 1, variationId = null) => {
    const response = await userApi.post(`/api/v1/users/cart/${productId}`, {
      quantity,
      variation_id: variationId
    });
    return response.data;
  },

  // Update cart item
  updateCartItem: async (cartItemId, quantity) => {
    const response = await userApi.put(`/api/v1/users/cart/${cartItemId}`, {
      quantity
    });
    return response.data;
  },

  // Remove from cart
  removeFromCart: async (cartItemId) => {
    const response = await userApi.delete(`/api/v1/users/cart/${cartItemId}`);
    return response.data;
  },

  // Clear cart
  clearCart: async () => {
    const response = await userApi.delete('/api/v1/users/cart');
    return response.data;
  },

  // Migrate session cart to user cart
  migrateCart: async () => {
    const response = await userApi.post('/api/v1/users/session/cart/migrate-to-user');
    return response.data;
  }
};
