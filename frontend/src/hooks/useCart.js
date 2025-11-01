import { useState, useEffect } from 'react';
import { cartService } from '../services/cartService';

export const useCart = () => {
  const [cart, setCart] = useState({ items: [], total: 0, total_items: 0 });
  const [loading, setLoading] = useState(false);

  const fetchCart = async () => {
    try {
      setLoading(true);
      const cartData = await cartService.getCart();
      setCart(cartData);
    } catch (error) {
      console.error('Error fetching cart:', error);
      // Fallback to empty cart
      setCart({ items: [], total: 0, total_items: 0 });
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async (productId, quantity = 1, variationId = null) => {
    try {
      setLoading(true);
      await cartService.addToCart(productId, quantity, variationId);
      await fetchCart(); // Refresh cart after adding
      return true;
    } catch (error) {
      console.error('Error adding to cart:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const updateCartItem = async (cartItemId, quantity) => {
    try {
      setLoading(true);
      await cartService.updateCartItem(cartItemId, quantity);
      await fetchCart();
    } catch (error) {
      console.error('Error updating cart:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const removeFromCart = async (cartItemId) => {
    try {
      setLoading(true);
      await cartService.removeFromCart(cartItemId);
      await fetchCart();
    } catch (error) {
      console.error('Error removing from cart:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const clearCart = async () => {
    try {
      setLoading(true);
      await cartService.clearCart();
      await fetchCart();
    } catch (error) {
      console.error('Error clearing cart:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCart();
  }, []);

  return {
    cart,
    loading,
    addToCart,
    updateCartItem,
    removeFromCart,
    clearCart,
    refreshCart: fetchCart
  };
};