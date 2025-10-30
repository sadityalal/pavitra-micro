import React from 'react'
import { Card, Button, Badge } from 'react-bootstrap'
import { Link } from 'react-router-dom'

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
    is_bestseller
  } = product

  const hasDiscount = compare_price && compare_price > base_price
  const discountPercent = hasDiscount
    ? Math.round(((compare_price - base_price) / compare_price) * 100)
    : 0

  // Fix image URL - always use relative paths for nginx proxy
  const getImageUrl = (url) => {
    if (!url) {
      console.log('🖼️ No image URL for product:', name)
      return '/images/placeholder-product.jpg'
    }

    // If it's a full URL with port 8002, extract the path
    if (url.includes('localhost:8002')) {
      const path = url.replace('http://localhost:8002', '')
      console.log('🖼️ Converted to path:', path)
      return path
    }

    // If it's already a relative path, use it as is
    if (url.startsWith('/uploads/')) {
      return url
    }

    // If missing leading slash, add it
    if (url.startsWith('uploads/')) {
      return `/${url}`
    }

    console.log('🖼️ Using fallback for URL:', url)
    return '/images/placeholder-product.jpg'
  }

  const [imageError, setImageError] = React.useState(false)

  const handleImageError = () => {
    console.error('❌ Image failed to load:', main_image_url)
    setImageError(true)
  }

  const handleImageLoad = () => {
    console.log('✅ Image loaded:', main_image_url)
  }

  const handleAddToCart = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (onAddToCart) {
      onAddToCart(product)
    }
  }

  const handleAddToWishlist = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (onAddToWishlist) {
      onAddToWishlist(product)
    }
  }

  const imageUrl = getImageUrl(main_image_url)
  const finalImageUrl = imageError ? '/images/placeholder-product.jpg' : imageUrl

  console.log(`🖼️ Product "${name}":`, {
    original: main_image_url,
    final: finalImageUrl,
    error: imageError
  })

  return (
    <Card className={`product-card h-100 ${className}`}>
      <div className="position-relative">
        <Card.Img
          variant="top"
          src={finalImageUrl}
          style={{ height: '200px', objectFit: 'cover' }}
          alt={name}
          onError={handleImageError}
          onLoad={handleImageLoad}
        />
        {}
        <div className="position-absolute top-0 start-0 p-2">
          {is_featured && <Badge bg="danger" className="me-1">Featured</Badge>}
          {is_bestseller && <Badge bg="warning" text="dark" className="me-1">Bestseller</Badge>}
          {hasDiscount && <Badge bg="success">{discountPercent}% OFF</Badge>}
        </div>
        {}
        <div className="position-absolute top-0 end-0 p-2">
          <Badge bg={stock_status === 'in_stock' ? 'success' : 'danger'}>
            {stock_status === 'in_stock' ? 'In Stock' : 'Out of Stock'}
          </Badge>
        </div>
      </div>
      <Card.Body className="d-flex flex-column">
        <Card.Title className="h6" style={{ minHeight: '48px' }}>
          <Link
            to={`/products/${id}`}
            className="text-decoration-none text-dark"
          >
            {name}
          </Link>
        </Card.Title>
        <Card.Text className="text-muted small flex-grow-1" style={{ minHeight: '40px' }}>
          {short_description?.substring(0, 100)}
          {short_description?.length > 100 && '...'}
        </Card.Text>
        <div className="mt-auto">
          {}
          <div className="d-flex align-items-center mb-2">
            <strong className="text-primary h5 mb-0">
              ₹{base_price}
            </strong>
            {hasDiscount && (
              <small className="text-muted text-decoration-line-through ms-2">
                ₹{compare_price}
              </small>
            )}
          </div>
          {}
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
              <Button
                variant="outline-secondary"
                size="sm"
                onClick={handleAddToWishlist}
              >
                <i className="fas fa-heart"></i>
              </Button>
            </div>
          )}
        </div>
      </Card.Body>
    </Card>
  )
}

export default ProductCard