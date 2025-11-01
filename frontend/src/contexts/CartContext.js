import React, { createContext, useContext, useState, useEffect } from 'react';
import { cartService } from '../services/cartService';

const CartContext = createContext();

export const useCartContext = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCartContext must be used within a CartProvider');
  }
  return context;
};

export const CartProvider = ({ children }) => {
  const [cart, setCart] = useState({
    items: [],
    subtotal: 0,
    total_items: 0
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchCart = async () => {
    try {
      setLoading(true);
      setError(null);
      const cartData = await cartService.getCart();
      console.log('CartContext: Fetched cart data:', cartData);

      setCart({
        items: cartData.items || [],
        subtotal: cartData.subtotal || 0,
        total_items: cartData.total_items || 0
      });
    } catch (error) {
      console.error('CartContext: Error fetching cart:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async (productId, quantity = 1, variationId = null) => {
    try {
      setLoading(true);
      setError(null);
      await cartService.addToCart(productId, quantity, variationId);
      // Refresh cart after successful add
      await fetchCart();
    } catch (error) {
      console.error('CartContext: Error adding to cart:', error);
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
      console.error('CartContext: Error updating cart:', error);
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
      console.error('CartContext: Error removing from cart:', error);
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
      console.error('CartContext: Error clearing cart:', error);
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Listen for cart update events
  useEffect(() => {
    const handleCartUpdate = () => {
      console.log('CartContext: Cart update event received, refreshing cart...');
      fetchCart();
    };

    document.addEventListener('cartUpdated', handleCartUpdate);

    return () => {
      document.removeEventListener('cartUpdated', handleCartUpdate);
    };
  }, []);

  // Initial cart fetch
  useEffect(() => {
    fetchCart();
  }, []);

  const value = {
    cart,
    loading,
    error,
    addToCart,
    updateCartItem,
    removeFromCart,
    clearCart,
    refreshCart: fetchCart
  };

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  );
};