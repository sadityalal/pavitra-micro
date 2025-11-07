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

  // ==== SESSION INITIALIZATION ON APP LOAD ====
  useEffect(() => {
    const initializeGuestSession = async () => {
      // Only initialize for guest users (no auth token)
      const token = localStorage.getItem('auth_token');
      if (!token && !sessionManager.getSession()) {
        try {
          console.log('🔄 Initializing guest session on app load...');
          // Make a simple API call to trigger session creation
          const response = await fetch('/api/v1/users/health', {
            credentials: 'include',
            headers: {
              'Content-Type': 'application/json',
            },
          });

          // Get session ID from response headers
          const sessionId = response.headers.get('x-session-id') ||
                           response.headers.get('x-secure-session-id');
          if (sessionId) {
            sessionManager.setSession(sessionId);
            console.log('✅ Guest session initialized on app load:', sessionId);

            // Fetch cart after session is ready
            fetchCart();
          }
        } catch (error) {
          console.error('❌ Failed to initialize guest session on app load:', error);
        }
      }
    };

    initializeGuestSession();
  }, []); // Empty dependency array - runs once when component mounts

  const fetchCart = async () => {
    try {
      setLoading(true);
      setError(null);

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

      await fetchCart();

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
      await fetchCart();

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
      await fetchCart();

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

  // Fetch cart when auth state changes
  useEffect(() => {
    console.log('🔄 Auth state changed, refreshing cart...', { isAuthenticated, userId: user?.id });
    fetchCart();
  }, [isAuthenticated, user?.id]);

  // Listen for cart update events
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
    refreshCart: fetchCart,
    findCartItemByProductId,
    getCartItemIdentifier
  };

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  );
};