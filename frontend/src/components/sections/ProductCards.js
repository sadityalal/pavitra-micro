import React from 'react';
import { formatCurrency, getStockStatusBadge, calculateSavings } from '../../utils/helpers';

const ProductCard = ({ product, onAddToCart, onAddToWishlist, loading = false }) => {
  const handleAddToCart = async (product) => {
    try {
      console.log('Adding product to cart:', product.id);

      // If onAddToCart callback is provided, use it
      if (onAddToCart) {
        await onAddToCart(product);
      } else {
        // Fallback: Show message that cart functionality needs to be implemented
        console.log('Add to cart functionality needs to be implemented');
        alert(`${product.name} would be added to cart!`);
      }
    } catch (error) {
      console.error('Failed to add to cart:', error);
      alert('Failed to add product to cart. Please try again.');
    }
  };

  const handleAddToWishlist = async (product) => {
    try {
      if (onAddToWishlist) {
        await onAddToWishlist(product);
      } else {
        console.log('Add to wishlist functionality not implemented');
      }
    } catch (error) {
      console.error('Failed to add to wishlist:', error);
    }
  };

  if (loading) {
    return (
      <div className="product-item">
        <div className="product-image placeholder-glow">
          <div className="placeholder" style={{ height: '250px' }}></div>
        </div>
        <div className="product-info">
          <div className="product-category placeholder placeholder-xs col-6"></div>
          <h4 className="product-name placeholder placeholder-xs col-8"></h4>
          <div className="product-rating placeholder placeholder-xs col-4"></div>
          <div className="product-price placeholder placeholder-xs col-5"></div>
        </div>
      </div>
    );
  }

  // Safe destructuring with defaults
  const {
    id,
    name = 'Product Name',
    slug = '',
    short_description,
    base_price = 0,
    compare_price,
    main_image_url,
    stock_status = 'in_stock',
    stock_quantity,
    is_featured = false,
    is_bestseller = false,
    is_trending = false
  } = product || {};

  const stockInfo = getStockStatusBadge(stock_status);
  const savings = calculateSavings(compare_price, base_price);
  const hasDiscount = compare_price && compare_price > base_price;

  const getImageUrl = (imagePath) => {
    if (!imagePath || imagePath === 'null' || imagePath === 'undefined') {
      return '/assets/img/product/placeholder.jpg';
    }
    if (imagePath.startsWith('http')) {
      return imagePath;
    }
    if (imagePath.startsWith('/uploads/')) {
      const backendUrl = process.env.REACT_APP_PRODUCT_URL || 'http://localhost:8002';
      return `${backendUrl}${imagePath}`;
    }
    return imagePath;
  };

  const imageUrl = getImageUrl(main_image_url);

  return (
    <div className="product-item">
      <div className="product-image">
        <div className="product-badges">
          {hasDiscount && (
            <span className="badge-sale">
              -{Math.round(((compare_price - base_price) / compare_price) * 100)}%
            </span>
          )}
          {is_featured && <span className="badge-new">New</span>}
          {is_bestseller && <span className="badge-trending">Trending</span>}
          {stock_status === 'out_of_stock' && (
            <span className="badge-out-of-stock">Out of Stock</span>
          )}
        </div>

        <img
          src={imageUrl}
          alt={name}
          className="img-fluid"
          loading="lazy"
          onError={(e) => {
            e.target.src = '/assets/img/product/placeholder.jpg';
          }}
        />

        <div className="product-actions">
          <button
            className="action-btn wishlist-btn"
            onClick={() => handleAddToWishlist(product)}
            title="Add to Wishlist"
          >
            <i className="bi bi-heart"></i>
          </button>
          <button
            className="action-btn compare-btn"
            title="Compare"
          >
            <i className="bi bi-arrow-left-right"></i>
          </button>
          <button
            className="action-btn quickview-btn"
            title="Quick View"
            onClick={() => window.location.href = `/product/${slug}`}
          >
            <i className="bi bi-zoom-in"></i>
          </button>
        </div>

        <button
          className={`cart-btn ${stock_status !== 'in_stock' ? 'disabled' : ''}`}
          onClick={() => handleAddToCart(product)}
          disabled={stock_status !== 'in_stock'}
        >
          {stock_status === 'in_stock' ? 'Add to Cart' : 'Out of Stock'}
        </button>
      </div>
      <div className="product-info">
        <div className="product-category">
          {is_featured ? 'Featured' : is_bestseller ? 'Best Seller' : 'Premium'}
        </div>

        <h4 className="product-name">
          <a href={`/product/${slug}`}>{name}</a>
        </h4>

        <div className="product-rating">
          <div className="stars">
            <i className="bi bi-star-fill"></i>
            <i className="bi bi-star-fill"></i>
            <i className="bi bi-star-fill"></i>
            <i className="bi bi-star-fill"></i>
            <i className="bi bi-star"></i>
          </div>
          <span className="rating-count">(24)</span>
        </div>

        <div className="product-price">
          {hasDiscount ? (
            <>
              <span className="old-price">{formatCurrency(compare_price)}</span>
              <span className="current-price">{formatCurrency(base_price)}</span>
            </>
          ) : (
            <span className="current-price">{formatCurrency(base_price)}</span>
          )}
        </div>

        <div className="color-swatches">
          <span className="swatch active" style={{ backgroundColor: '#2563eb' }}></span>
          <span className="swatch" style={{ backgroundColor: '#059669' }}></span>
          <span className="swatch" style={{ backgroundColor: '#dc2626' }}></span>
        </div>
      </div>
    </div>
  );
};

export default ProductCard;