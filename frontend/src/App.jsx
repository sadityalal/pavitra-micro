import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import axios from 'axios'
import BaseLayout from './components/BaseLayout'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import Products from './pages/Products'
import ProductDetail from './pages/ProductDetail'
import Cart from './pages/Cart'
import Account from './pages/Account'
import './index.css'

function App() {
  const [user, setUser] = useState(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      axios.get('http://localhost:8001/api/v1/auth/users/me', {
        headers: { Authorization: `Bearer ${token}` }
      })
      .then(response => setUser(response.data))
      .catch(() => localStorage.removeItem('token'))
    }
  }, [])

  return (
    <Router>
      <BaseLayout user={user} setUser={setUser}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login setUser={setUser} />} />
          <Route path="/register" element={<Register setUser={setUser} />} />
          <Route path="/products" element={<Products user={user} />} />
          <Route path="/product/:slug" element={<ProductDetail user={user} />} />
          <Route path="/cart" element={<Cart user={user} />} />
          <Route path="/account/*" element={<Account user={user} />} />
          <Route path="/about" element={<div className="container py-5"><h1>About Us</h1></div>} />
          <Route path="/contact" element={<div className="container py-5"><h1>Contact Us</h1></div>} />
        </Routes>
      </BaseLayout>
    </Router>
  )
}

export default App
