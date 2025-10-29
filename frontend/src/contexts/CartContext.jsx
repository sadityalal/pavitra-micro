import React, { createContext, useContext, useState, useEffect } from 'react'
import { useAuth } from './AuthContext'
import { API } from '../services/api'
import useLocalStorage from '../hooks/useLocalStorage'

const CartContext = createContext()

export const useCart = () => {
  const context = useContext(CartContext)
  if (!context) {
    throw new Error('useCart must be used within a CartProvider')
  }
  return context
}

export const CartProvider = ({ children }) => {
  const { user, isAuthenticated } = useAuth()
  const [guestId, setGuestId] = useLocalStorage('guest_id', null)
  const [cart, setCart] = useState({ items: [], subtotal: 0, total_items: 0 })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Generate guest ID if not exists
  useEffect(() => {
    if (!isAuthenticated && !guestId) {
      const newGuestId = `guest_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      setGuestId(newGuestId)
    }
  }, [isAuthenticated, guestId, setGuestId])

  // Load cart when authentication status changes
  useEffect(() => {
    loadCart()
  }, [isAuthenticated, user, guestId])

  const getAuthHeaders = () => {
    const headers = {}

    if (!isAuthenticated && guestId) {
      headers['X-Guest-ID'] = guestId
    }

    return headers
  }

  const loadCart = async () => {
    try {
      setLoading(true)
      let response

      if (isAuthenticated) {
        response = await API.users.getCart()
      } else if (guestId) {
        // For guests, we'll handle cart in localStorage and sync on login
        const guestCart = JSON.parse(localStorage.getItem(`guest_cart_${guestId}`) || '{"items": [], "subtotal": 0, "total_items": 0}')
        setCart(guestCart)
        return
      } else {
        setCart({ items: [], subtotal: 0, total_items: 0 })
        return
      }

      setCart(response.data)
    } catch (err) {
      setError('Failed to load cart')
      console.error('Cart load error:', err)
    } finally {
      setLoading(false)
    }
  }

  const addToCart = async (productId, quantity = 1, variationId = null) => {
    try {
      setError('')

      if (isAuthenticated) {
        await API.users.addToCart(productId, quantity)
      } else {
        // Handle guest cart in localStorage
        const guestCart = JSON.parse(localStorage.getItem(`guest_cart_${guestId}`) || '{"items": [], "subtotal": 0, "total_items": 0}')

        // Check if item already exists
        const existingItemIndex = guestCart.items.findIndex(
          item => item.product_id === productId && item.variation_id === variationId
        )

        if (existingItemIndex > -1) {
          // Update quantity
          guestCart.items[existingItemIndex].quantity += quantity
          guestCart.items[existingItemIndex].total_price =
            guestCart.items[existingItemIndex].unit_price * guestCart.items[existingItemIndex].quantity
        } else {
          // Get product details (you might want to cache this)
          const productResponse = await API.products.getById(productId)
          const product = productResponse.data

          // Add new item
          guestCart.items.push({
            id: Date.now(), // Temporary ID for guest
            product_id: productId,
            variation_id: variationId,
            product_name: product.name,
            product_slug: product.slug,
            product_image: product.main_image_url,
            unit_price: product.base_price,
            quantity: quantity,
            total_price: product.base_price * quantity,
            stock_quantity: product.stock_quantity,
            stock_status: product.stock_status,
            max_cart_quantity: product.max_cart_quantity || 10,
            variation_attributes: null // You can enhance this for variations
          })
        }

        // Recalculate totals
        guestCart.subtotal = guestCart.items.reduce((sum, item) => sum + item.total_price, 0)
        guestCart.total_items = guestCart.items.reduce((sum, item) => sum + item.quantity, 0)

        localStorage.setItem(`guest_cart_${guestId}`, JSON.stringify(guestCart))
        setCart(guestCart)
      }

      await loadCart() // Reload to get updated cart
      return { success: true }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to add to cart'
      setError(errorMsg)
      return { success: false, error: errorMsg }
    }
  }

  const updateCartItem = async (itemId, quantity) => {
    try {
      setError('')

      if (isAuthenticated) {
        await API.users.updateCartItem(itemId, quantity)
      } else {
        const guestCart = JSON.parse(localStorage.getItem(`guest_cart_${guestId}`) || '{"items": []}')
        const itemIndex = guestCart.items.findIndex(item => item.id === itemId)

        if (itemIndex > -1) {
          if (quantity === 0) {
            // Remove item
            guestCart.items.splice(itemIndex, 1)
          } else {
            // Update quantity
            guestCart.items[itemIndex].quantity = quantity
            guestCart.items[itemIndex].total_price =
              guestCart.items[itemIndex].unit_price * quantity
          }

          // Recalculate totals
          guestCart.subtotal = guestCart.items.reduce((sum, item) => sum + item.total_price, 0)
          guestCart.total_items = guestCart.items.reduce((sum, item) => sum + item.quantity, 0)

          localStorage.setItem(`guest_cart_${guestId}`, JSON.stringify(guestCart))
          setCart(guestCart)
        }
      }

      await loadCart()
      return { success: true }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to update cart'
      setError(errorMsg)
      return { success: false, error: errorMsg }
    }
  }

  const removeFromCart = async (itemId) => {
    return await updateCartItem(itemId, 0)
  }

  const clearCart = async () => {
    try {
      setError('')

      if (isAuthenticated) {
        await API.users.clearCart()
      } else {
        localStorage.setItem(`guest_cart_${guestId}`, JSON.stringify({ items: [], subtotal: 0, total_items: 0 }))
        setCart({ items: [], subtotal: 0, total_items: 0 })
      }

      await loadCart()
      return { success: true }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to clear cart'
      setError(errorMsg)
      return { success: false, error: errorMsg }
    }
  }

  const syncGuestCart = async () => {
    if (!isAuthenticated || !guestId) return

    try {
      const guestCart = JSON.parse(localStorage.getItem(`guest_cart_${guestId}`) || '{"items": []}')

      // Add all guest cart items to user cart
      for (const item of guestCart.items) {
        await API.users.addToCart(item.product_id, item.quantity, item.variation_id)
      }

      // Clear guest cart
      localStorage.removeItem(`guest_cart_${guestId}`)
      setGuestId(null)

      // Reload user cart
      await loadCart()
    } catch (err) {
      console.error('Failed to sync guest cart:', err)
    }
  }

  // Sync guest cart when user logs in
  useEffect(() => {
    if (isAuthenticated && guestId) {
      syncGuestCart()
    }
  }, [isAuthenticated, guestId])

  const value = {
    cart,
    loading,
    error,
    addToCart,
    updateCartItem,
    removeFromCart,
    clearCart,
    loadCart,
    guestId,
    isGuest: !isAuthenticated
  }

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  )
}