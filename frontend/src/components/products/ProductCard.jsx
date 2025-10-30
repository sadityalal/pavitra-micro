// frontend/src/components/products/ProductCard.jsx
import React, { useState } from 'react'
import { Card, Button, Badge } from 'react-bootstrap'
import { Link } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { useCart } from '../../contexts/CartContext'
import { API } from '../../services/api'
import { getImageUrl } from '../../config/api'

const ProductCard = ({
  product,
  onAddToCart,
  onAddToWishlist,
  showActions = true,
  className = ''
}) => {
  const {
    id,
    name,
    short_description,
    base_price,
    compare_price,
    main_image_url,
    stock_status,
    slug,
    is_featured,
    is_bestseller,
    category
  } = product

  const { isAuthenticated } = useAuth()
  const { addToCart } = useCart()
  const [imageError, setImageError] = useState(false)
  const [imageLoading, setImageLoading] = useState(true)
  const [addingToWishlist, setAddingToWishlist] = useState(false)

  const hasDiscount = compare_price && compare_price > base_price
  const discountPercent = hasDiscount
    ? Math.round(((compare_price - base_price) / compare_price) * 100)
    : 0

  const imageUrl = getImageUrl(main_image_url)
  const finalImageUrl = imageError ? '/static/img/product/placeholder.jpg' : imageUrl

  const handleImageError = () => {
    setImageError(true)
    setImageLoading(false)
  }

  const handleImageLoad = () => {
    setImageLoading(false)
    setImageError(false)
  }

  const handleAddToCart = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (onAddToCart) {
      onAddToCart(product)
    } else {
      await addToCart(id, 1)
    }
  }

  const handleAddToWishlist = async (e) => {
    e.preventDefault()
    e.stopPropagation()

    if (!isAuthenticated) {
      alert('Please login to add items to wishlist')
      return
    }

    if (onAddToWishlist) {
      onAddToWishlist(product)
    } else {
      try {
        setAddingToWishlist(true)
        await API.users.addToWishlist(id)
        // You might want to show a success message here
      } catch (error) {
        console.error('Error adding to wishlist:', error)
      } finally {
        setAddingToWishlist(false)
      }
    }
  }

  return (
    <Card className={`product-card h-100 ${className}`}>
      <div className="position-relative">
        <div className="image-container">
          {imageLoading && (
            <div className="image-placeholder">
              <div className="spinner-border text-primary" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
            </div>
          )}
          <Card.Img
            variant="top"
            src={finalImageUrl}
            alt={name}
            onError={handleImageError}
            onLoad={handleImageLoad}
            style={{ display: imageLoading ? 'none' : 'block' }}
          />
        </div>

        {/* Product Badges */}
        <div className="product-badges">
          {is_featured && <Badge bg="danger" className="me-1">Featured</Badge>}
          {is_bestseller && <Badge bg="warning" text="dark" className="me-1">Bestseller</Badge>}
          {hasDiscount && <Badge bg="success">{discountPercent}% OFF</Badge>}
        </div>

        {/* Stock Status */}
        <div className="stock-badge">
          <Badge bg={stock_status === 'in_stock' ? 'success' : 'danger'}>
            {stock_status === 'in_stock' ? 'In Stock' : 'Out of Stock'}
          </Badge>
        </div>

        {/* Product Actions */}
        {showActions && (
          <div className="product-actions">
            <Button
              variant="outline-secondary"
              size="sm"
              onClick={handleAddToWishlist}
              disabled={addingToWishlist}
              className="action-btn"
            >
              <i className={`bi ${addingToWishlist ? 'bi-heart-fill' : 'bi-heart'}`}></i>
            </Button>
            <Button
              variant="outline-secondary"
              size="sm"
              as={Link}
              to={`/products/${id}`}
              className="action-btn"
            >
              <i className="bi bi-eye"></i>
            </Button>
          </div>
        )}
      </div>

      <Card.Body className="d-flex flex-column">
        <div className="product-category small text-muted mb-1">
          {category?.name || 'Uncategorized'}
        </div>

        <Card.Title className="h6 product-name">
          <Link
            to={`/products/${id}`}
            className="text-decoration-none text-dark"
          >
            {name}
          </Link>
        </Card.Title>

        <Card.Text className="text-muted small flex-grow-1 product-description">
          {short_description?.substring(0, 100)}
          {short_description?.length > 100 && '...'}
        </Card.Text>

        <div className="mt-auto">
          <div className="d-flex align-items-center mb-2 price-section">
            <strong className="text-primary h5 mb-0 current-price">
              ₹{base_price}
            </strong>
            {hasDiscount && (
              <small className="text-muted text-decoration-line-through ms-2 original-price">
                ₹{compare_price}
              </small>
            )}
          </div>

          {showActions && (
            <div className="d-flex gap-2">
              <Button
                variant="primary"
                size="sm"
                className="flex-fill"
                onClick={handleAddToCart}
                disabled={stock_status !== 'in_stock'}
              >
                <i className="fas fa-shopping-cart me-1"></i>
                Add to Cart
              </Button>
            </div>
          )}
        </div>
      </Card.Body>
    </Card>
  )
}

export default ProductCard