import React, { createContext, useContext, useState, useEffect } from 'react'

const CartContext = createContext()

export const useCart = () => {
  const context = useContext(CartContext)
  if (!context) {
    throw new Error('useCart must be used within a CartProvider')
  }
  return context
}

export const CartProvider = ({ children }) => {
  const [cartCount, setCartCount] = useState(0)
  const [wishlistCount, setWishlistCount] = useState(0)
  const [cartItems, setCartItems] = useState([])

  useEffect(() => {
    // Load cart from localStorage or API
    const savedCart = localStorage.getItem('pavitra_cart')
    if (savedCart) {
      const cart = JSON.parse(savedCart)
      setCartItems(cart)
      setCartCount(cart.reduce((total, item) => total + item.quantity, 0))
    }

    // Load wishlist count
    const savedWishlist = localStorage.getItem('pavitra_wishlist')
    if (savedWishlist) {
      const wishlist = JSON.parse(savedWishlist)
      setWishlistCount(wishlist.length)
    }
  }, [])

  const addToCart = (product, quantity = 1) => {
    const existingItem = cartItems.find(item => item.id === product.id)
    let newCartItems

    if (existingItem) {
      newCartItems = cartItems.map(item =>
        item.id === product.id 
          ? { ...item, quantity: item.quantity + quantity }
          : item
      )
    } else {
      newCartItems = [...cartItems, { ...product, quantity }]
    }

    setCartItems(newCartItems)
    setCartCount(newCartItems.reduce((total, item) => total + item.quantity, 0))
    localStorage.setItem('pavitra_cart', JSON.stringify(newCartItems))
  }

  const removeFromCart = (productId) => {
    const newCartItems = cartItems.filter(item => item.id !== productId)
    setCartItems(newCartItems)
    setCartCount(newCartItems.reduce((total, item) => total + item.quantity, 0))
    localStorage.setItem('pavitra_cart', JSON.stringify(newCartItems))
  }

  const updateCartQuantity = (productId, quantity) => {
    if (quantity <= 0) {
      removeFromCart(productId)
      return
    }

    const newCartItems = cartItems.map(item =>
      item.id === productId ? { ...item, quantity } : item
    )
    setCartItems(newCartItems)
    setCartCount(newCartItems.reduce((total, item) => total + item.quantity, 0))
    localStorage.setItem('pavitra_cart', JSON.stringify(newCartItems))
  }

  const value = {
    cartCount,
    wishlistCount,
    cartItems,
    addToCart,
    removeFromCart,
    updateCartQuantity,
    setWishlistCount
  }

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  )
}
