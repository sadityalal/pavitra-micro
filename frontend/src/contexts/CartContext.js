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
  const [sessionInitialized, setSessionInitialized] = useState(false);

  // Initialize session for guest users
  const initializeSession = async () => {
    if (sessionInitialized || localStorage.getItem('auth_token')) {
      return;
    }

    try {
      console.log('🔄 Initializing guest session...');
      // Make a simple API call to ensure session is created
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
      }
    } catch (error) {
      console.error('❌ Failed to initialize guest session:', error);
    }
  };

  const fetchCart = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Ensure session is initialized for guest users
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
    } catch (error) {
      console.error('🛒 CartContext: Error fetching cart:', error);
      
      // Don't reset cart on session errors - try to reinitialize
      if (error.response?.status === 401 || error.message?.includes('session')) {
        console.log('🔄 Session may be expired, trying to reinitialize...');
        setSessionInitialized(false);
        // Don't set error for session issues to avoid UI disruption
      } else {
        setError(error.message);
        // Reset cart only on non-session errors
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

  const addToCart = async (productId, quantity = 1, variationId = null) => {
    try {
      setLoading(true);
      setError(null);
      console.log('🛒 Adding to cart with session cookies...');
      
      // Ensure session is initialized for guest users
      if (!localStorage.getItem('auth_token') && !sessionInitialized) {
        await initializeSession();
      }

      const result = await cartService.addToCart(productId, quantity, variationId);
      console.log('🛒 Add to cart result:', result);
      
      // Refresh cart after successful addition
      await fetchCart();
      
      return result;
    } catch (error) {
      console.error('🛒 CartContext: Error adding to cart:', error);
      
      // If it's a session issue, try to reinitialize and retry once
      if ((error.response?.status === 401 || error.message?.includes('session')) && !sessionInitialized) {
        console.log('🔄 Session issue detected, reinitializing and retrying...');
        setSessionInitialized(false);
        
        // Small delay before retry
        await new Promise(resolve => setTimeout(resolve, 500));
        
        try {
          await initializeSession();
          const retryResult = await cartService.addToCart(productId, quantity, variationId);
          await fetchCart();
          return retryResult;
        } catch (retryError) {
          console.error('🛒 Retry failed:', retryError);
          setError(retryError.message);
          throw retryError;
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
      
      // Ensure session is initialized for guest users
      if (!localStorage.getItem('auth_token') && !sessionInitialized) {
        await initializeSession();
      }

      await cartService.updateCartItem(cartItemId, quantity);
      await fetchCart();
    } catch (error) {
      console.error('🛒 CartContext: Error updating cart:', error);
      
      // Handle session issues
      if (error.response?.status === 401 || error.message?.includes('session')) {
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
      
      // Ensure session is initialized for guest users
      if (!localStorage.getItem('auth_token') && !sessionInitialized) {
        await initializeSession();
      }

      await cartService.removeFromCart(cartItemId);
      await fetchCart();
    } catch (error) {
      console.error('🛒 CartContext: Error removing from cart:', error);
      
      // Handle session issues
      if (error.response?.status === 401 || error.message?.includes('session')) {
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
      
      // Ensure session is initialized for guest users
      if (!localStorage.getItem('auth_token') && !sessionInitialized) {
        await initializeSession();
      }

      await cartService.clearCart();
      await fetchCart();
    } catch (error) {
      console.error('🛒 CartContext: Error clearing cart:', error);
      
      // Handle session issues
      if (error.response?.status === 401 || error.message?.includes('session')) {
        setSessionInitialized(false);
      }
      
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Debug function to check session status
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

    document.addEventListener('cartUpdated', handleCartUpdate);
    
    return () => {
      document.removeEventListener('cartUpdated', handleCartUpdate);
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
    addToCart,
    updateCartItem,
    removeFromCart,
    clearCart,
    refreshCart: fetchCart,
    debugSession,
    initializeSession
  };

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  );
};