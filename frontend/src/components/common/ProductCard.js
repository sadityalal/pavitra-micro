import React, { useState } from 'react';
import { formatCurrency } from '../../utils/helpers';
import { useCartContext } from '../../contexts/CartContext';

const ProductCard = ({ product, onAddToCart, onAddToWishlist, loading = false }) => {
  const { addToCart } = useCartContext();
  const [addingToCart, setAddingToCart] = useState(false);

  const handleAddToCart = async (product) => {
    if (product.stock_status !== 'in_stock') {
      alert('This product is out of stock');
      return;
    }

    try {
      setAddingToCart(true);
      console.log('ProductCard: Adding product to cart:', product.id);
      await addToCart(product.id, 1);
      console.log('ProductCard: Product added to cart successfully');
      if (onAddToCart) {
        onAddToCart(product);
      }
    } catch (error) {
      console.error('ProductCard: Failed to add to cart:', error);
      if (error.message.includes('session') || error.message.includes('Session')) {
        alert('Please refresh the page and try again. Session issue detected.');
      } else {
        alert(error.message || 'Failed to add product to cart');
      }
    } finally {
      setAddingToCart(false);
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

  const {
    name,
    slug,
    base_price,
    compare_price,
    main_image_url,
    stock_status,
    is_featured,
    is_bestseller
  } = product;

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
          <button className="action-btn wishlist-btn" title="Add to Wishlist">
            <i className="bi bi-heart"></i>
          </button>
          <button className="action-btn compare-btn" title="Compare">
            <i className="bi bi-arrow-left-right"></i>
          </button>
          <button className="action-btn quickview-btn" title="Quick View">
            <i className="bi bi-zoom-in"></i>
          </button>
        </div>
        <button
          className={`cart-btn ${stock_status !== 'in_stock' ? 'disabled' : ''}`}
          onClick={() => handleAddToCart(product)}
          disabled={stock_status !== 'in_stock' || addingToCart}
        >
          {addingToCart ? (
            <>
              <span className="spinner-border spinner-border-sm me-2"></span>
              Adding...
            </>
          ) : stock_status === 'in_stock' ? (
            'Add to Cart'
          ) : (
            'Out of Stock'
          )}
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
      </div>
    </div>
  );
};

export default ProductCard;