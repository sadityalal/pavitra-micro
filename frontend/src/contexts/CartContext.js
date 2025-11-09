import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { cartService } from '../services/cartService';
import { sessionManager } from '../services/api';
import { useAuth } from './AuthContext';

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
  const { isAuthenticated, user } = useAuth();
  const fetchInProgress = useRef(false);
  const lastCartHash = useRef('');

  // Calculate a simple hash of cart data to detect actual changes
  const getCartHash = (cartData) => {
    return JSON.stringify({
      items: cartData.items,
      total_items: cartData.total_items,
      subtotal: cartData.subtotal
    });
  };

  const fetchCart = async (force = false) => {
    if (fetchInProgress.current && !force) {
      console.log('🛒 Fetch already in progress, skipping...');
      return;
    }

    try {
      fetchInProgress.current = true;
      setLoading(true);
      setError(null);

      const currentSession = sessionManager.getSession();
      console.log('🛒 CartContext: Fetching cart with session:', currentSession);

      const cartData = await cartService.getCart();
      console.log('🛒 CartContext: Fetched cart data:', cartData);

      const newCartHash = getCartHash(cartData);

      // Only update state if cart data actually changed
      if (force || newCartHash !== lastCartHash.current) {
        setCart({
          items: cartData.items || [],
          subtotal: cartData.subtotal || 0,
          total_items: cartData.total_items || 0
        });
        lastCartHash.current = newCartHash;
      } else {
        console.log('🛒 Cart data unchanged, skipping state update');
      }
    } catch (error) {
      console.error('🛒 CartContext: Error fetching cart:', error);
      setError(error.message);
      // Don't reset cart on error to maintain current state
    } finally {
      setLoading(false);
      fetchInProgress.current = false;
    }
  };

  const addToCart = async (productId, quantity = 1, variationId = null) => {
    try {
      setLoading(true);
      setError(null);
      console.log('🛒 Adding to cart with shared session...');
      const result = await cartService.addToCart(productId, quantity, variationId);
      console.log('🛒 Add to cart result:', result);

      // Force refresh cart after adding item
      await fetchCart(true);

      const event = new CustomEvent('cartUpdated', {
        detail: {
          action: 'add',
          productId,
          quantity
        }
      });
      document.dispatchEvent(event);
      return result;
    } catch (error) {
      console.error('🛒 CartContext: Error adding to cart:', error);
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const updateCartItem = async (cartItemId, newQuantity) => {
    try {
      setLoading(true);
      setError(null);
      console.log('🛒 Updating cart item:', { cartItemId, newQuantity });

      if (newQuantity < 1) {
        await cartService.removeFromCart(cartItemId);
      } else {
        await cartService.updateCartItem(cartItemId, newQuantity);
      }

      // Force refresh cart after update
      await fetchCart(true);

      const event = new CustomEvent('cartUpdated', {
        detail: {
          action: 'update',
          cartItemId,
          newQuantity
        }
      });
      document.dispatchEvent(event);
    } catch (error) {
      console.error('🛒 CartContext: Error updating cart:', error);
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
      console.log('🛒 Removing cart item:', cartItemId);
      await cartService.removeFromCart(cartItemId);

      // Force refresh cart after removal
      await fetchCart(true);

      const event = new CustomEvent('cartUpdated', {
        detail: {
          action: 'remove',
          cartItemId
        }
      });
      document.dispatchEvent(event);
    } catch (error) {
      console.error('🛒 CartContext: Error removing from cart:', error);
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

      // Force refresh cart after clear
      await fetchCart(true);

      const event = new CustomEvent('cartUpdated', {
        detail: { action: 'clear' }
      });
      document.dispatchEvent(event);
    } catch (error) {
      console.error('🛒 CartContext: Error clearing cart:', error);
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const findCartItemByProductId = (productId, variationId = null) => {
    if (!cart.items || cart.items.length === 0) return null;

    return cart.items.find(item => {
      const matchesProduct = item.product_id === productId;
      const matchesVariation = variationId ?
        item.variation_id === variationId :
        !item.variation_id;
      return matchesProduct && matchesVariation;
    });
  };

  const getCartItemIdentifier = (item) => {
    if (isAuthenticated) {
      return item.id;
    } else {
      return `guest_${item.product_id}_${item.variation_id || 'no_var'}`;
    }
  };

  // Fix for image URLs in cart items
  const processCartItems = (items) => {
    if (!items || !Array.isArray(items)) return [];

    return items.map(item => {
      // Fix image URL if needed
      if (item.product_image) {
        // Ensure the image URL is properly formatted
        if (item.product_image.startsWith('/uploads/')) {
          const backendUrl = process.env.REACT_APP_PRODUCT_URL || 'http://localhost:8002';
          item.product_image = `${backendUrl}${item.product_image}`;
        }
        // Handle cases where image might be null or undefined
        if (item.product_image === 'null' || item.product_image === 'undefined') {
          item.product_image = '/assets/img/product/placeholder.jpg';
        }
      } else {
        item.product_image = '/assets/img/product/placeholder.jpg';
      }

      return item;
    });
  };

  // Initialize cart on mount - only once
  useEffect(() => {
    console.log('🛒 CartProvider: Initializing cart...');
    fetchCart(true);
  }, []);

  // Only refresh cart when auth state changes significantly
  useEffect(() => {
    console.log('🔄 Auth state changed, refreshing cart...', { isAuthenticated, userId: user?.id });
    fetchCart(true);
  }, [isAuthenticated, user?.id]);

  // Single event listener for cart updates - properly cleaned up
  useEffect(() => {
    const handleCartUpdate = (event) => {
      console.log('🛒 CartContext: Cart update event received:', event.detail);
      // Only refresh if it's a significant update
      if (event.detail.action === 'clear' || event.detail.action === 'migrate') {
        fetchCart(true);
      }
    };

    const handleAuthStateChange = (event) => {
      console.log('🔐 CartContext: Auth state change event received:', event.detail);
      if (event.detail.action === 'logout') {
        setCart({
          items: [],
          subtotal: 0,
          total_items: 0
        });
        sessionManager.clearSession();
        lastCartHash.current = '';
      } else if (event.detail.action === 'login' || event.detail.action === 'register') {
        // Wait a bit for cart migration to complete
        setTimeout(() => {
          console.log('🔄 CartContext: Refreshing cart after auth state change');
          fetchCart(true);
        }, 1000);
      }
    };

    document.addEventListener('cartUpdated', handleCartUpdate);
    document.addEventListener('authStateChanged', handleAuthStateChange);

    return () => {
      document.removeEventListener('cartUpdated', handleCartUpdate);
      document.removeEventListener('authStateChanged', handleAuthStateChange);
    };
  }, []);

  // Process cart items for display with proper image URLs
  const displayCart = {
    ...cart,
    items: processCartItems(cart.items)
  };

  const value = {
    cart: displayCart,
    loading,
    error,
    addToCart,
    updateCartItem,
    removeFromCart,
    clearCart,
    refreshCart: () => fetchCart(true),
    findCartItemByProductId,
    getCartItemIdentifier
  };

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  );
};