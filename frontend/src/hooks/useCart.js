import { useState, useEffect } from 'react';
import { cartService } from '../services/cartService';

export const useCart = () => {
  const [cart, setCart] = useState({
    items: [],
    total: 0,
    total_items: 0,
    subtotal: 0,
    shipping_cost: 0
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchCart = async () => {
    try {
      setLoading(true);
      setError(null);
      const cartData = await cartService.getCart();
      console.log('Fetched cart data:', cartData);

      // Ensure cart data has proper structure
      setCart({
        items: cartData.items || [],
        total: cartData.total || 0,
        total_items: cartData.total_items || 0,
        subtotal: cartData.subtotal || 0,
        shipping_cost: cartData.shipping_cost || 0
      });
    } catch (error) {
      console.error('Error fetching cart:', error);
      setError(error.message);
      // Don't reset cart on error to prevent UI flickering
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async (productId, quantity = 1, variationId = null) => {
    try {
      setLoading(true);
      setError(null);

      await cartService.addToCart(productId, quantity, variationId);

      // Refresh cart after adding item
      await fetchCart();

      return true;
    } catch (error) {
      console.error('Error adding to cart:', error);
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const updateCartItem = async (cartItemId, quantity) => {
    try {
      setLoading(true);
      setError(null);
      await cartService.updateCartItem(cartItemId, quantity);
      await fetchCart();
    } catch (error) {
      console.error('Error updating cart:', error);
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const removeFromCart = async (cartItemId) => {
    try {
      setLoading(true);
      setError(null);
      await cartService.removeFromCart(cartItemId);
      await fetchCart();
    } catch (error) {
      console.error('Error removing from cart:', error);
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const clearCart = async () => {
    try {
      setLoading(true);
      setError(null);
      await cartService.clearCart();
      await fetchCart();
    } catch (error) {
      console.error('Error clearing cart:', error);
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Initialize cart on component mount
  useEffect(() => {
    fetchCart();
  }, []);

  return {
    cart,
    loading,
    error,
    addToCart,
    updateCartItem,
    removeFromCart,
    clearCart,
    refreshCart: fetchCart
  };
};