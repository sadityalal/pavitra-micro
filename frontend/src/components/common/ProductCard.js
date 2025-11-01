// frontend/src/components/common/ProductCard.js
import React from 'react';
import { formatCurrency, getStockStatusBadge, calculateSavings } from '../../utils/helpers';

const ProductCard = ({ product, onAddToCart, onAddToWishlist, loading = false }) => {
  if (loading) {
    return (
      <div className="product-item loading">
        <div className="product-image placeholder-glow">
          <div className="placeholder" style={{ height: '200px' }}></div>
        </div>
        <div className="product-info p-3">
          <div className="placeholder placeholder-xs col-8"></div>
          <div className="placeholder placeholder-xs col-6 mt-2"></div>
          <div className="placeholder placeholder-xs col-4 mt-2"></div>
        </div>
      </div>
    );
  }

  const {
    id,
    name,
    slug,
    short_description,
    base_price,
    sale_price,
    main_image_url,
    stock_status,
    stock_quantity,
    rating,
    review_count,
    discount_percentage
  } = product;

  const stockInfo = getStockStatusBadge(stock_status);
  const savings = calculateSavings(base_price, sale_price);
  const finalPrice = sale_price || base_price;
  const hasDiscount = sale_price && sale_price < base_price;

  return (
    <div className="product-item" data-aos="fade-up">
      <div className="product-image position-relative">
        <img
          src={main_image_url || '/assets/img/product/placeholder.jpg'}
          alt={name}
          className="img-fluid"
          loading="lazy"
          onError={(e) => {
            e.target.src = '/assets/img/product/placeholder.jpg';
          }}
        />
        
        <div className="product-badges position-absolute top-0 start-0 p-2">
          {hasDiscount && (
            <span className="badge bg-danger me-1">-{discount_percentage}%</span>
          )}
          {stock_status === 'in_stock' && stock_quantity < 10 && (
            <span className="badge bg-warning">Low Stock</span>
          )}
        </div>
        
        <div className="position-absolute top-0 end-0 p-2">
          <span className={`badge ${stockInfo.class}`}>
            {stockInfo.text}
          </span>
        </div>
        
        <div className="product-actions position-absolute bottom-0 start-0 end-0 p-2">
          <div className="d-flex justify-content-center gap-2">
            <button
              className="action-btn wishlist-btn"
              onClick={() => onAddToWishlist && onAddToWishlist(product)}
              title="Add to Wishlist"
              disabled={!onAddToWishlist}
            >
              <i className="bi bi-heart"></i>
            </button>
            <button
              className="action-btn quickview-btn"
              title="Quick View"
            >
              <i className="bi bi-zoom-in"></i>
            </button>
          </div>
        </div>
        
        <button
          className={`cart-btn w-100 ${stock_status !== 'in_stock' ? 'disabled' : ''}`}
          onClick={() => onAddToCart && onAddToCart(product)}
          disabled={stock_status !== 'in_stock' || !onAddToCart}
        >
          {stock_status === 'in_stock' ? 'Add to Cart' : 'Out of Stock'}
        </button>
      </div>
      
      <div className="product-info p-3">
        <h4 className="product-name h6 mb-2">
          <a href={`/product/${slug}`} className="text-decoration-none text-dark">
            {name}
          </a>
        </h4>
        
        {rating > 0 && (
          <div className="product-rating d-flex align-items-center mb-2">
            <div className="stars text-warning">
              {[1, 2, 3, 4, 5].map((star) => (
                <i
                  key={star}
                  className={`bi ${star <= rating ? 'bi-star-fill' : 'bi-star'}`}
                ></i>
              ))}
            </div>
            <span className="rating-count text-muted small ms-1">
              ({review_count || 0})
            </span>
          </div>
        )}
        
        <div className="product-price mb-2">
          {hasDiscount ? (
            <>
              <span className="current-price fw-bold text-dark fs-5">
                {formatCurrency(sale_price)}
              </span>
              <span className="old-price text-muted text-decoration-line-through ms-2">
                {formatCurrency(base_price)}
              </span>
              {savings > 0 && (
                <div className="savings text-success small">
                  Save {formatCurrency(savings)}
                </div>
              )}
            </>
          ) : (
            <span className="current-price fw-bold text-dark fs-5">
              {formatCurrency(base_price)}
            </span>
          )}
        </div>
        
        {short_description && (
          <p className="product-short-desc small text-muted mb-0">
            {short_description}
          </p>
        )}
      </div>
    </div>
  );
};

export default ProductCard;