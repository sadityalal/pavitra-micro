import React, { createContext, useContext, useState, useEffect } from 'react';
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

  const initializeSession = async () => {
    try {
      console.log('🔄 Initializing session via user service...');
      const response = await fetch('/api/v1/users/health', {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (response.ok) {
        const sessionId = response.headers.get('x-session-id');
        if (sessionId) {
          sessionManager.setSession(sessionId);
          console.log('✅ Session initialized with ID:', sessionId);
        } else {
          console.log('✅ Session initialized (no ID returned)');
        }
        return true;
      }
      return false;
    } catch (error) {
      console.error('❌ Failed to initialize session:', error);
      return false;
    }
  };

  // Add this function to ensure session is always available
  const ensureSession = async () => {
    if (!isAuthenticated && !sessionManager.getSession()) {
      console.log('🔄 Ensuring guest session for cart operations...');
      return await initializeSession();
    }
    return true;
  };

  const fetchCart = async () => {
    try {
      setLoading(true);
      setError(null);
      if (!isAuthenticated && !sessionManager.getSession()) {
        await initializeSession();
      }
      const cartData = await cartService.getCart();
      console.log('🛒 CartContext: Fetched cart data:', cartData);
      setCart({
        items: cartData.items || [],
        subtotal: cartData.subtotal || 0,
        total_items: cartData.total_items || 0
      });
    } catch (error) {
      console.error('🛒 CartContext: Error fetching cart:', error);
      setError(error.message);
      setCart({
        items: [],
        subtotal: 0,
        total_items: 0
      });
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async (productId, quantity = 1, variationId = null) => {
    try {
      setLoading(true);
      setError(null);

      // Ensure session exists before adding to cart
      await ensureSession();

      console.log('🛒 Adding to cart with shared session...');
      const result = await cartService.addToCart(productId, quantity, variationId);
      console.log('🛒 Add to cart result:', result);
      await fetchCart();

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

  const updateCartItem = async (cartItemId, quantity) => {
    try {
      setLoading(true);
      setError(null);
      await cartService.updateCartItem(cartItemId, quantity);
      await fetchCart();
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
      await cartService.removeFromCart(cartItemId);
      await fetchCart();
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
      await fetchCart();
    } catch (error) {
      console.error('🛒 CartContext: Error clearing cart:', error);
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isAuthenticated) {
      initializeSession();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    console.log('🔄 Auth state changed, refreshing cart...', { isAuthenticated, userId: user?.id });
    fetchCart();
  }, [isAuthenticated, user?.id]);

  useEffect(() => {
    const handleCartUpdate = () => {
      console.log('🛒 CartContext: Cart update event received, refreshing cart...');
      fetchCart();
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
      }
      fetchCart();
    };

    document.addEventListener('cartUpdated', handleCartUpdate);
    document.addEventListener('authStateChanged', handleAuthStateChange);

    return () => {
      document.removeEventListener('cartUpdated', handleCartUpdate);
      document.removeEventListener('authStateChanged', handleAuthStateChange);
    };
  }, []);

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
    refreshCart: fetchCart,
    initializeSession,
    ensureSession
  };

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  );
};