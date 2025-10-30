import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Container, Row, Col, Card, Button, Form, Badge, Alert } from 'react-bootstrap'
import { API } from '../services/api'
import { useCart } from '../contexts/CartContext'
import { useAuth } from '../contexts/AuthContext'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'

const ProductDetail = () => {
  const { id } = useParams()
  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [quantity, setQuantity] = useState(1)
  const [selectedVariation, setSelectedVariation] = useState(null)
  const { addToCart } = useCart()
  const { isAuthenticated } = useAuth()

  useEffect(() => {
    loadProduct()
  }, [id])

  const loadProduct = async () => {
    try {
      setLoading(true)
      const response = await API.products.getById(id)
      setProduct(response.data)
      if (response.data.variations && response.data.variations.length > 0) {
        setSelectedVariation(response.data.variations[0])
      }
    } catch (err) {
      setError('Product not found')
      console.error('Error loading product:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAddToCart = async () => {
    try {
      const productId = selectedVariation ? selectedVariation.id : product.id
      const result = await addToCart(productId, quantity, selectedVariation?.id)
      if (result.success) {
        console.log('Product added to cart')
      }
    } catch (err) {
      console.error('Error adding to cart:', err)
    }
  }

  const handleAddToWishlist = async () => {
    if (!isAuthenticated) {
      return
    }
    try {
      await API.users.addToWishlist(product.id)
      console.log('Product added to wishlist')
    } catch (err) {
      console.error('Error adding to wishlist:', err)
    }
  }

  if (loading) return <LoadingSpinner text="Loading product..." />
  if (error) return <ErrorMessage error={error} />

  return (
    <Container className="my-5">
      <Row>
        <Col md={6}>
          <Card>
            <Card.Img
              variant="top"
              src={product.main_image_url || '/images/placeholder-product.jpg'}
              style={{ height: '400px', objectFit: 'contain' }}
              alt={product.name}
            />
          </Card>
        </Col>
        <Col md={6}>
          <div className="mb-3">
            {product.is_featured && <Badge bg="danger" className="me-2">Featured</Badge>}
            {product.is_bestseller && <Badge bg="warning" text="dark" className="me-2">Bestseller</Badge>}
            <Badge bg={product.stock_status === 'in_stock' ? 'success' : 'danger'}>
              {product.stock_status === 'in_stock' ? 'In Stock' : 'Out of Stock'}
            </Badge>
          </div>
          <h1 className="h2">{product.name}</h1>
          <p className="text-muted">{product.short_description}</p>
          <div className="mb-3">
            <h3 className="text-primary">₹{product.base_price}</h3>
            {product.compare_price && product.compare_price > product.base_price && (
              <small className="text-muted text-decoration-line-through me-2">
                ₹{product.compare_price}
              </small>
            )}
          </div>
          {product.variations && product.variations.length > 0 && (
            <div className="mb-3">
              <h6>Variations:</h6>
              <div className="d-flex gap-2">
                {product.variations.map(variation => (
                  <Button
                    key={variation.id}
                    variant={selectedVariation?.id === variation.id ? 'primary' : 'outline-primary'}
                    size="sm"
                    onClick={() => setSelectedVariation(variation)}
                  >
                    {variation.attributes?.color || variation.attributes?.size || 'Default'}
                  </Button>
                ))}
              </div>
            </div>
          )}
          <div className="mb-3">
            <Row className="align-items-center">
              <Col xs="auto">
                <Form.Label>Quantity:</Form.Label>
              </Col>
              <Col xs="auto">
                <Form.Select
                  value={quantity}
                  onChange={(e) => setQuantity(parseInt(e.target.value))}
                  style={{ width: '80px' }}
                >
                  {[...Array(10)].map((_, i) => (
                    <option key={i + 1} value={i + 1}>
                      {i + 1}
                    </option>
                  ))}
                </Form.Select>
              </Col>
            </Row>
          </div>
          <div className="d-flex gap-2 mb-4">
            <Button
              variant="primary"
              size="lg"
              onClick={handleAddToCart}
              disabled={product.stock_status !== 'in_stock'}
            >
              <i className="fas fa-shopping-cart me-2"></i>
              Add to Cart
            </Button>
            <Button
              variant="outline-secondary"
              size="lg"
              onClick={handleAddToWishlist}
            >
              <i className="fas fa-heart"></i>
            </Button>
          </div>
          <Card>
            <Card.Body>
              <h6>Product Details</h6>
              <div dangerouslySetInnerHTML={{ __html: product.description }} />
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  )
}

export default ProductDetail