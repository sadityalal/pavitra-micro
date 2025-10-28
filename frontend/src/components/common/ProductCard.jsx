import React from 'react';
import { Link } from 'react-router-dom';
import { getImageUrl } from '../../utils/imageHelper';

const ProductCard = ({ product, onAddToCart, onAddToWishlist }) => {
  const formatPrice = (price) => `${product?.currency_symbol || '₹'}${parseFloat(price || 0).toFixed(2)}`;

  const mainImageUrl = getImageUrl(product.main_image_url);

  return (
    <div className="product-card">
      <Link to={`/products/${product.slug || product.id}`} className="product-image-link">
        <div className="product-image">
          <img
            src={mainImageUrl}
            alt={product.name}
            className="img-fluid"
            onError={(e) => {
              e.currentTarget.src = '/static/img/product/placeholder.jpg';
            }}
          />
          {product.compare_price && product.compare_price > product.base_price && (
            <span className="badge-sale">-{Math.round((1 - product.base_price / product.compare_price) * 100)}%</span>
          )}
        </div>
      </Link>

      <div className="product-info">
        <h5><Link to={`/products/${product.slug || product.id}`}>{product.name}</Link></h5>
        <p className="price">{formatPrice(product.base_price)}</p>
        <div className="d-flex gap-2">
          <button className="btn btn-sm btn-outline-primary" onClick={() => onAddToCart && onAddToCart(product)}>Add</button>
          <button className="btn btn-sm btn-outline-secondary" onClick={() => onAddToWishlist && onAddToWishlist(product.id)}><i className="bi bi-heart"></i></button>
        </div>
      </div>
    </div>
  );
};

export default ProductCard;