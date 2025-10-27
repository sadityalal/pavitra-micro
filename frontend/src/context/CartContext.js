import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from './AuthContext';

const CartContext = createContext();

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};

export const CartProvider = ({ children }) => {
  const [cart, setCart] = useState({ items: [], subtotal: 0, total_items: 0 });
  const [loading, setLoading] = useState(false);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      loadCart();
    } else {
      // Load cart from localStorage for guests
      const guestCart = localStorage.getItem('guestCart');
      if (guestCart) {
        setCart(JSON.parse(guestCart));
      }
    }
  }, [isAuthenticated]);

  const loadCart = async () => {
    if (!isAuthenticated) return;
    
    setLoading(true);
    try {
      const cartData = await api.getCart();
      setCart(cartData);
    } catch (error) {
      console.error('Failed to load cart:', error);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async (productId, quantity = 1) => {
    try {
      if (isAuthenticated) {
        await api.addToCart(productId, quantity);
        await loadCart(); // Reload cart after addition
      } else {
        // Handle guest cart in localStorage
        const guestCart = JSON.parse(localStorage.getItem('guestCart') || '{"items": [], "subtotal": 0, "total_items": 0}');
        
        // Simple guest cart implementation - you might want to enhance this
        const existingItem = guestCart.items.find(item => item.product_id === productId);
        
        if (existingItem) {
          existingItem.quantity += quantity;
        } else {
          guestCart.items.push({
            product_id: productId,
            quantity: quantity,
            product_name: `Product ${productId}`,
            product_price: 0, // You'd need to get actual product data
            total_price: 0
          });
        }
        
        // Recalculate totals
        guestCart.subtotal = guestCart.items.reduce((sum, item) => sum + item.total_price, 0);
        guestCart.total_items = guestCart.items.reduce((sum, item) => sum + item.quantity, 0);
        
        localStorage.setItem('guestCart', JSON.stringify(guestCart));
        setCart(guestCart);
      }
      
      return { success: true };
    } catch (error) {
      console.error('Failed to add to cart:', error);
      return { success: false, error: error.message };
    }
  };

  const updateCartItem = async (cartItemId, quantity) => {
    try {
      if (isAuthenticated) {
        await api.updateCartItem(cartItemId, quantity);
        await loadCart();
      } else {
        // Update guest cart
        const guestCart = JSON.parse(localStorage.getItem('guestCart') || '{"items": []}');
        const item = guestCart.items.find(item => item.id === cartItemId);
        
        if (item) {
          if (quantity === 0) {
            guestCart.items = guestCart.items.filter(item => item.id !== cartItemId);
          } else {
            item.quantity = quantity;
            item.total_price = item.product_price * quantity;
          }
          
          guestCart.subtotal = guestCart.items.reduce((sum, item) => sum + item.total_price, 0);
          guestCart.total_items = guestCart.items.reduce((sum, item) => sum + item.quantity, 0);
          
          localStorage.setItem('guestCart', JSON.stringify(guestCart));
          setCart(guestCart);
        }
      }
      
      return { success: true };
    } catch (error) {
      console.error('Failed to update cart item:', error);
      return { success: false, error: error.message };
    }
  };

  const removeFromCart = async (cartItemId) => {
    try {
      if (isAuthenticated) {
        await api.removeFromCart(cartItemId);
        await loadCart();
      } else {
        // Remove from guest cart
        const guestCart = JSON.parse(localStorage.getItem('guestCart') || '{"items": []}');
        guestCart.items = guestCart.items.filter(item => item.id !== cartItemId);
        
        guestCart.subtotal = guestCart.items.reduce((sum, item) => sum + item.total_price, 0);
        guestCart.total_items = guestCart.items.reduce((sum, item) => sum + item.quantity, 0);
        
        localStorage.setItem('guestCart', JSON.stringify(guestCart));
        setCart(guestCart);
      }
      
      return { success: true };
    } catch (error) {
      console.error('Failed to remove from cart:', error);
      return { success: false, error: error.message };
    }
  };

  const clearCart = async () => {
    try {
      if (isAuthenticated) {
        await api.clearCart();
        await loadCart();
      } else {
        localStorage.removeItem('guestCart');
        setCart({ items: [], subtotal: 0, total_items: 0 });
      }
      
      return { success: true };
    } catch (error) {
      console.error('Failed to clear cart:', error);
      return { success: false, error: error.message };
    }
  };

  const value = {
    cart,
    loading,
    addToCart,
    updateCartItem,
    removeFromCart,
    clearCart,
    reloadCart: loadCart
  };

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  );
};
