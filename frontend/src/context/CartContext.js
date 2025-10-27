import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { userService } from '../services/userService';
import { useAuth } from './AuthContext';

const CartContext = createContext();

const cartReducer = (state, action) => {
  switch (action.type) {
    case 'SET_CART':
      return {
        ...state,
        items: action.payload.items || [],
        subtotal: action.payload.subtotal || 0,
        totalItems: action.payload.total_items || 0,
        loading: false
      };
    
    case 'ADD_ITEM':
      const existingItem = state.items.find(item => 
        item.product_id === action.payload.product_id && 
        item.variation_id === action.payload.variation_id
      );

      if (existingItem) {
        const updatedItems = state.items.map(item =>
          item.id === existingItem.id
            ? { ...item, quantity: item.quantity + action.payload.quantity }
            : item
        );
        
        return {
          ...state,
          items: updatedItems,
          totalItems: state.totalItems + action.payload.quantity,
          subtotal: state.subtotal + (action.payload.product_price * action.payload.quantity)
        };
      } else {
        return {
          ...state,
          items: [...state.items, action.payload],
          totalItems: state.totalItems + action.payload.quantity,
          subtotal: state.subtotal + (action.payload.product_price * action.payload.quantity)
        };
      }
    
    case 'UPDATE_ITEM':
      const itemToUpdate = state.items.find(item => item.id === action.payload.cartItemId);
      if (!itemToUpdate) return state;

      const quantityDiff = action.payload.quantity - itemToUpdate.quantity;
      const updatedItems = state.items.map(item =>
        item.id === action.payload.cartItemId
          ? { ...item, quantity: action.payload.quantity }
          : item
      ).filter(item => item.quantity > 0);

      return {
        ...state,
        items: updatedItems,
        totalItems: state.totalItems + quantityDiff,
        subtotal: state.subtotal + (itemToUpdate.product_price * quantityDiff)
      };
    
    case 'REMOVE_ITEM':
      const itemToRemove = state.items.find(item => item.id === action.payload);
      if (!itemToRemove) return state;

      return {
        ...state,
        items: state.items.filter(item => item.id !== action.payload),
        totalItems: state.totalItems - itemToRemove.quantity,
        subtotal: state.subtotal - (itemToRemove.product_price * itemToRemove.quantity)
      };
    
    case 'CLEAR_CART':
      return {
        items: [],
        subtotal: 0,
        totalItems: 0,
        loading: false
      };
    
    case 'SET_LOADING':
      return {
        ...state,
        loading: action.payload
      };
    
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        loading: false
      };
    
    default:
      return state;
  }
};

const initialState = {
  items: [],
  subtotal: 0,
  totalItems: 0,
  loading: false,
  error: null
};

export const CartProvider = ({ children }) => {
  const [state, dispatch] = useReducer(cartReducer, initialState);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      loadCart();
    } else {
      // Clear cart when user logs out
      dispatch({ type: 'CLEAR_CART' });
    }
  }, [isAuthenticated]);

  const loadCart = async () => {
    if (!isAuthenticated) return;
    
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const cartData = await userService.getCart();
      dispatch({ type: 'SET_CART', payload: cartData });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
    }
  };

  const addToCart = async (productId, quantity = 1, productData = null) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      if (isAuthenticated) {
        await userService.addToCart(productId, quantity);
        await loadCart(); // Reload cart from server
      } else {
        // For guest users, add to local state
        if (productData) {
          dispatch({
            type: 'ADD_ITEM',
            payload: {
              id: Date.now(), // Temporary ID for guest
              product_id: productId,
              product_name: productData.name,
              product_price: productData.base_price,
              quantity: quantity,
              product_image: productData.main_image_url
            }
          });
        }
      }
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
      throw error;
    }
  };

  const updateCartItem = async (cartItemId, quantity) => {
    try {
      if (isAuthenticated) {
        await userService.updateCartItem(cartItemId, quantity);
        await loadCart();
      } else {
        dispatch({
          type: 'UPDATE_ITEM',
          payload: { cartItemId, quantity }
        });
      }
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
      throw error;
    }
  };

  const removeFromCart = async (cartItemId) => {
    try {
      if (isAuthenticated) {
        await userService.removeFromCart(cartItemId);
        await loadCart();
      } else {
        dispatch({ type: 'REMOVE_ITEM', payload: cartItemId });
      }
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
      throw error;
    }
  };

  const clearCart = async () => {
    try {
      if (isAuthenticated) {
        await userService.clearCart();
      }
      dispatch({ type: 'CLEAR_CART' });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
      throw error;
    }
  };

  const value = {
    ...state,
    addToCart,
    updateCartItem,
    removeFromCart,
    clearCart,
    refreshCart: loadCart
  };

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};
