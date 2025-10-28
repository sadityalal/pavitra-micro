import React from 'react';
import { Link } from 'react-router-dom';
import { getImageUrl } from '../../utils/imageHelper';

const BestSellers = ({ featuredProducts = [], siteSettings = {}, onAddToCart, onAddToWishlist, totalItems = 0 }) => {
  const formatPrice = (price) => `${siteSettings.currency_symbol || '₹'}${parseFloat(price || 0).toFixed(2)}`;

  return (
    <section id="best-sellers" className="best-sellers section">
      <div className="container section-title" data-aos="fade-up">
        <h2>Best Sellers</h2>
        <p>Our most popular products loved by customers</p>
      </div>

      <div className="container" data-aos="fade-up" data-aos-delay="100">
        <div className="row g-5">
          {featuredProducts.slice(0, 4).map((product) => {
            const productImageUrl = getImageUrl(product.main_image_url);

            return (
              <div className="col-lg-3 col-md-6" key={product.id}>
                <div className="product-item" style={{cursor: 'pointer'}}>
                  <div className="product-image">
                    {product.compare_price && product.compare_price > product.base_price && (
                      <div className="product-badge sale-badge">{Math.round((1 - product.base_price / product.compare_price) * 100)}% Off</div>
                    )}
                    {product.is_featured && !product.compare_price && (
                      <div className="product-badge">Featured</div>
                    )}
                    <img
                      src={productImageUrl}
                      alt={product.name}
                      className="img-fluid"
                      loading="lazy"
                      onError={(e) => e.currentTarget.src = '/static/img/product/placeholder.jpg'}
                    />

                    <div className="product-actions">
                      <button className="action-btn wishlist-btn" onClick={() => onAddToWishlist && onAddToWishlist(product.id)}><i className="bi bi-heart"></i></button>
                      <Link to={`/products/${product.slug || product.id}`} className="action-btn quickview-btn"><i className="bi bi-eye"></i></Link>
                    </div>

                    {product.stock_quantity > 0 ? (
                      <button className="cart-btn" onClick={() => onAddToCart && onAddToCart(product)}>Add to Cart</button>
                    ) : (
                      <button className="cart-btn" disabled>Out of Stock</button>
                    )}
                  </div>

                  <div className="product-info">
                    <div className="product-category">{product.category_name || product.category?.name || 'Uncategorized'}</div>
                    <h4 className="product-name"><Link to={`/products/${product.slug || product.id}`}>{product.name}</Link></h4>
                    <div className="product-rating">
                      <div className="stars">{[...Array(5)].map((_, i) => (<i key={i} className={`bi bi-star${i < (product.average_rating || 0) ? '-fill' : ''}`}></i>))}</div>
                      <span className="rating-count">({product.review_count || 0})</span>
                    </div>
                    <div className="product-price">
                      {product.compare_price && product.compare_price > product.base_price && (<span className="old-price">{formatPrice(product.compare_price)}</span>)}
                      <span className="current-price">{formatPrice(product.base_price)}</span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="text-center mt-5" data-aos="fade-up" data-aos-delay="200">
          <Link to="/products" className="btn btn-outline-primary">View All Products</Link>
        </div>
      </div>
    </section>
  );
};

export default BestSellers;