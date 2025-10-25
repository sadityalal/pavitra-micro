import React, { useState, useEffect } from 'react'
import axios from 'axios'

function Products({ user }) {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchProducts()
  }, [])

  const fetchProducts = async () => {
    try {
      const response = await axios.get('http://localhost:8002/api/v1/products/products')
      setProducts(response.data.products || [])
    } catch (error) {
      console.error('Failed to fetch products:', error)
      setProducts([])
    } finally {
      setLoading(false)
    }
  }

  const addToCart = async (productId) => {
    if (!user) {
      alert('Please login to add items to cart')
      return
    }

    try {
      await axios.post(`http://localhost:8004/api/v1/users/cart/${productId}`, {}, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      })
      alert('Product added to cart!')
    } catch (error) {
      alert('Failed to add to cart: ' + (error.response?.data?.detail || 'Unknown error'))
    }
  }

  if (loading) return <div className="container" style={{padding: '2rem', textAlign: 'center'}}>Loading products...</div>

  return (
    <div className="container">
      <h1 style={{padding: '2rem 0'}}>Our Products</h1>
      
      <div className="products-grid">
        {products.map(product => (
          <div key={product.id} className="product-card">
            <div className="product-image">
              {product.main_image_url ? (
                <img src={product.main_image_url} alt={product.name} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
              ) : (
                'No Image'
              )}
            </div>
            <div className="product-name">{product.name}</div>
            <div className="product-price">₹{product.base_price}</div>
            <p style={{color: '#666', fontSize: '0.9rem', margin: '0.5rem 0'}}>
              {product.short_description}
            </p>
            <button 
              onClick={() => addToCart(product.id)} 
              className="btn"
              style={{width: '100%', marginTop: '1rem'}}
            >
              Add to Cart
            </button>
          </div>
        ))}
      </div>

      {products.length === 0 && (
        <div style={{textAlign: 'center', padding: '3rem', color: '#666'}}>
          No products found. Make sure the product service is running.
        </div>
      )}
    </div>
  )
}

export default Products
