import React, { createContext, useContext, useState, useEffect } from 'react';
import { cartService } from '../services/cartService';
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
  const [sessionInitialized, setSessionInitialized] = useState(false);
  const [sessionIssue, setSessionIssue] = useState(false);

  const { isAuthenticated, user } = useAuth();

  const initializeSession = async () => {
    if (sessionInitialized || localStorage.getItem('auth_token')) {
      return;
    }
    try {
      console.log('🔄 Initializing guest session...');
      const response = await fetch(
        `${process.env.REACT_APP_PRODUCT_URL || 'http://localhost:8002'}/api/v1/products/featured?page_size=1`,
        {
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      if (response.ok) {
        console.log('✅ Guest session initialized successfully');
        setSessionInitialized(true);
        setSessionIssue(false);
      }
    } catch (error) {
      console.error('❌ Failed to initialize guest session:', error);
      setSessionIssue(true);
    }
  };

  const recoverSession = async () => {
    try {
      console.log('🔄 Attempting session recovery...');
      setSessionInitialized(false);
      await initializeSession();
      if (sessionInitialized) {
        console.log('✅ Session recovered successfully');
        setSessionIssue(false);
        return true;
      }
    } catch (error) {
      console.error('❌ Session recovery failed:', error);
      setSessionIssue(true);
      return false;
    }
  };

  const fetchCart = async () => {
    try {
      setLoading(true);
      setError(null);
      if (!localStorage.getItem('auth_token') && !sessionInitialized) {
        await initializeSession();
      }
      const cartData = await cartService.getCart();
      console.log('🛒 CartContext: Fetched cart data:', cartData);
      setCart({
        items: cartData.items || [],
        subtotal: cartData.subtotal || 0,
        total_items: cartData.total_items || 0
      });
      setSessionIssue(false);
    } catch (error) {
      console.error('🛒 CartContext: Error fetching cart:', error);
      if (error.response?.status === 401 || error.message?.includes('session')) {
        console.log('🔄 Session may be expired, trying to reinitialize...');
        setSessionIssue(true);
        setSessionInitialized(false);

        // Try to recover session
        await recoverSession();
      } else {
        setError(error.message);
        setCart({
          items: [],
          subtotal: 0,
          total_items: 0
        });
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    console.log('🔄 Auth state changed, refreshing cart...', { isAuthenticated, userId: user?.id });
    fetchCart();
  }, [isAuthenticated, user?.id]);

  const addToCart = async (productId, quantity = 1, variationId = null) => {
    try {
      setLoading(true);
      setError(null);
      console.log('🛒 Adding to cart with session cookies...');

      if (!localStorage.getItem('auth_token') && !sessionInitialized) {
        await initializeSession();
      }

      const result = await cartService.addToCart(productId, quantity, variationId);
      console.log('🛒 Add to cart result:', result);
      await fetchCart();

      // Dispatch cart updated event for real-time updates
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

      // If session issue, try to recover and retry once
      if ((error.response?.status === 401 || error.message?.includes('session')) && !sessionInitialized) {
        console.log('🔄 Session issue detected, attempting recovery and retry...');
        const recovered = await recoverSession();
        if (recovered) {
          try {
            console.log('🔄 Retrying add to cart after session recovery...');
            const retryResult = await cartService.addToCart(productId, quantity, variationId);
            await fetchCart();
            return retryResult;
          } catch (retryError) {
            console.error('🛒 Retry failed after session recovery:', retryError);
            setError(retryError.message);
            throw retryError;
          }
        }
      } else {
        setError(error.message);
        throw error;
      }
    } finally {
      setLoading(false);
    }
  };

  const updateCartItem = async (cartItemId, quantity) => {
    try {
      setLoading(true);
      setError(null);
      if (!localStorage.getItem('auth_token') && !sessionInitialized) {
        await initializeSession();
      }
      await cartService.updateCartItem(cartItemId, quantity);
      await fetchCart();
    } catch (error) {
      console.error('🛒 CartContext: Error updating cart:', error);
      if (error.response?.status === 401 || error.message?.includes('session')) {
        setSessionIssue(true);
        setSessionInitialized(false);
      }
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
      if (!localStorage.getItem('auth_token') && !sessionInitialized) {
        await initializeSession();
      }
      await cartService.removeFromCart(cartItemId);
      await fetchCart();
    } catch (error) {
      console.error('🛒 CartContext: Error removing from cart:', error);
      if (error.response?.status === 401 || error.message?.includes('session')) {
        setSessionIssue(true);
        setSessionInitialized(false);
      }
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
      if (!localStorage.getItem('auth_token') && !sessionInitialized) {
        await initializeSession();
      }
      await cartService.clearCart();
      await fetchCart();
    } catch (error) {
      console.error('🛒 CartContext: Error clearing cart:', error);
      if (error.response?.status === 401 || error.message?.includes('session')) {
        setSessionIssue(true);
        setSessionInitialized(false);
      }
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const debugSession = async () => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_USER_URL || 'http://localhost:8004'}/api/v1/users/session/debug`,
        {
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      if (response.ok) {
        const sessionInfo = await response.json();
        console.log('🔍 CartContext Session Debug:', sessionInfo);
        return sessionInfo;
      }
    } catch (error) {
      console.error('❌ Session debug failed:', error);
    }
    return null;
  };

  useEffect(() => {
    const handleCartUpdate = () => {
      console.log('🛒 CartContext: Cart update event received, refreshing cart...');
      fetchCart();
    };

    const handleAuthStateChange = (event) => {
      console.log('🔐 CartContext: Auth state change event received:', event.detail);
      if (event.detail.action === 'logout') {
        // Clear cart immediately on logout
        setCart({
          items: [],
          subtotal: 0,
          total_items: 0
        });
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
    sessionInitialized,
    sessionIssue,
    addToCart,
    updateCartItem,
    removeFromCart,
    clearCart,
    refreshCart: fetchCart,
    debugSession,
    initializeSession,
    recoverSession
  };

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  );
};