import React, { useState, useEffect } from 'react'
import { Container, Row, Col, Button } from 'react-bootstrap'
import { API } from '../services/api'
import PageHeader from '../components/layout/PageHeader'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'
import EmptyState from '../components/common/EmptyState'
import ProductCard from '../components/products/ProductCard'
import { useCart } from '../contexts/CartContext'

const Wishlist = () => {
  const [wishlist, setWishlist] = useState({ items: [], total_count: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [removing, setRemoving] = useState({})
  const { addToCart } = useCart()

  useEffect(() => {
    loadWishlist()
  }, [])

  const loadWishlist = async () => {
    try {
      setLoading(true)
      const response = await API.users.getWishlist()
      setWishlist(response.data)
    } catch (err) {
      setError('Failed to load wishlist')
    } finally {
      setLoading(false)
    }
  }

  const removeFromWishlist = async (productId) => {
    try {
      setRemoving(prev => ({ ...prev, [productId]: true }))
      await API.users.removeFromWishlist(productId)
      await loadWishlist()
    } catch (err) {
      setError('Failed to remove from wishlist')
    } finally {
      setRemoving(prev => ({ ...prev, [productId]: false }))
    }
  }

  const handleAddToCart = async (product) => {
    const result = await addToCart(product.id, 1)
    if (result.success) {
      // Optional: Remove from wishlist after adding to cart
      // await removeFromWishlist(product.id)
    }
  }

  const handleAddAllToCart = async () => {
    for (const item of wishlist.items) {
      await addToCart(item.product_id, 1)
    }
    alert('All items added to cart!')
  }

  if (loading) {
    return (
      <>
        <PageHeader title="My Wishlist" />
        <LoadingSpinner text="Loading your wishlist..." />
      </>
    )
  }

  return (
    <>
      <PageHeader title="My Wishlist" />
      <Container>
        <ErrorMessage error={error} onRetry={loadWishlist} />

        {wishlist.items.length === 0 ? (
          <EmptyState
            icon="fas fa-heart"
            title="Your wishlist is empty"
            message="Save items you love to your wishlist. Review them anytime and easily move them to your cart."
            actionText="Browse Products"
            onAction={() => window.location.href = '/products'}
          />
        ) : (
          <>
            <div className="d-flex justify-content-between align-items-center mb-4">
              <h5>{wishlist.total_count} items in wishlist</h5>
              <Button variant="primary" onClick={handleAddAllToCart}>
                <i className="fas fa-shopping-cart me-2"></i>
                Add All to Cart
              </Button>
            </div>

            <Row>
              {wishlist.items.map((item) => (
                <Col key={item.id} xl={3} lg={4} md={6} className="mb-4">
                  <ProductCard
                    product={{
                      id: item.product_id,
                      name: item.product_name,
                      short_description: '',
                      base_price: item.product_price,
                      main_image_url: item.product_image,
                      stock_status: item.product_stock_status,
                      slug: item.product_slug,
                      is_featured: false,
                      is_bestseller: false
                    }}
                    onAddToCart={handleAddToCart}
                    onAddToWishlist={() => removeFromWishlist(item.product_id)}
                    className="position-relative"
                  />

                  <Button
                    variant="outline-danger"
                    size="sm"
                    className="position-absolute"
                    style={{ top: '10px', right: '10px', zIndex: 10 }}
                    onClick={() => removeFromWishlist(item.product_id)}
                    disabled={removing[item.product_id]}
                  >
                    <i className="fas fa-trash"></i>
                  </Button>
                </Col>
              ))}
            </Row>
          </>
        )}
      </Container>
    </>
  )
}

export default Wishlist