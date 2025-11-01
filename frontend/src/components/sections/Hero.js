import React from 'react';
import { useProducts } from '../../hooks/useProducts';
import { useSettings } from '../../contexts/SettingsContext';
import { useCart } from '../../hooks/useCart';

const Hero = () => {
  const { products: featuredProducts, loading } = useProducts('featured');
  const { frontendSettings } = useSettings();
  const { addToCart } = useCart();

  const handleAddToCart = async (product) => {
    try {
      await addToCart(product.id, 1);
      console.log('Product added to cart:', product.name);
      // You can add a toast notification here later
    } catch (error) {
      console.error('Failed to add to cart:', error);
      // You can add error handling/notification here
    }
  };

  const toggleSearch = () => {
    console.log('Toggle search');
  };

  if (loading) {
    return (
      <section id="hero" className="hero section">
        <div className="container text-center py-5">
          <div className="spinner-border" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </section>
    );
  }

  const mainProduct = featuredProducts[0];
  const secondaryProducts = featuredProducts.slice(1, 3);

  return (
    <section id="hero" className="hero section">
      <div className="hero-container">
        <div className="hero-content">
          <div className="content-wrapper" data-aos="fade-up" data-aos-delay="100">
            <h1 className="hero-title">Welcome to {frontendSettings.site_name || 'Pavitra Enterprises'}</h1>
            <p className="hero-description">
              Discover our curated collection of premium products designed to enhance your lifestyle.
              From electronics to fashion, find everything you need with exclusive deals and fast shipping.
            </p>
            <div className="hero-actions" data-aos="fade-up" data-aos-delay="200">
              <a href="/products" className="btn-primary">Shop Now</a>
              <a href="/products?featured=true" className="btn-secondary">Featured Products</a>
            </div>
            <div className="features-list" data-aos="fade-up" data-aos-delay="300">
              <div className="feature-item">
                <i className="bi bi-truck"></i>
                <span>Free Shipping Over {frontendSettings.currency_symbol}{frontendSettings.free_shipping_min_amount || '500'}</span>
              </div>
              <div className="feature-item">
                <i className="bi bi-arrow-clockwise"></i>
                <span>{frontendSettings.return_period_days || '10'}-Day Returns</span>
              </div>
              <div className="feature-item">
                <i className="bi bi-shield-check"></i>
                <span>Secure Payment</span>
              </div>
            </div>
          </div>
        </div>
        <div className="hero-visuals">
          <div className="product-showcase" data-aos="fade-left" data-aos-delay="200">
            {mainProduct ? (
              <div className="product-card featured">
                <img
                  src={mainProduct.main_image_url || '/assets/img/product/placeholder.jpg'}
                  alt={mainProduct.name}
                  className="img-fluid"
                  onError={(e) => {
                    e.target.src = '/assets/img/product/placeholder.jpg';
                  }}
                />
                <div className="product-badge">Best Seller</div>
                <div className="product-info">
                  <h4>{mainProduct.name}</h4>
                  <div className="price">
                    <span className="sale-price">{frontendSettings.currency_symbol}{mainProduct.base_price}</span>
                    {mainProduct.compare_price && mainProduct.compare_price > mainProduct.base_price && (
                      <span className="original-price">{frontendSettings.currency_symbol}{mainProduct.compare_price}</span>
                    )}
                  </div>
                  <button
                      className="btn btn-dark"
                      onClick={() => handleAddToCart(mainProduct)}
                      disabled={mainProduct.stock_status !== 'in_stock'}
                    >
                      <i className="bi bi-cart-plus me-2"></i>
                      {mainProduct.stock_status === 'in_stock' ? 'Add to Cart' : 'Out of Stock'}
                    </button>
                </div>
              </div>
            ) : (
              <div className="product-card featured">
                <img src="/assets/img/product/placeholder.jpg" alt="Featured Product" className="img-fluid" />
                <div className="product-badge">Featured</div>
                <div className="product-info">
                  <h4>Featured Products</h4>
                  <div className="price">
                    <span className="sale-price">Explore Now</span>
                  </div>
                  <button className="btn btn-dark" onClick={() => window.location.href = '/products'}>
                      <i className="bi bi-cart-plus me-2"></i>
                      Shop Now
                    </button>
                </div>
              </div>
            )}
            <div className="product-grid">
              {secondaryProducts.map((product, index) => (
                <div
                  key={product.id}
                  className="product-mini"
                  data-aos="zoom-in"
                  data-aos-delay={400 + index * 100}
                  onClick={() => handleAddToCart(product)}
                  style={{ cursor: 'pointer' }}
                >
                  <img
                    src={product.main_image_url || '/assets/img/product/placeholder.jpg'}
                    alt={product.name}
                    className="img-fluid"
                    onError={(e) => {
                      e.target.src = '/assets/img/product/placeholder.jpg';
                    }}
                  />
                  <span className="mini-price">{frontendSettings.currency_symbol}{product.base_price}</span>
                </div>
              ))}
              {/* Add placeholder products if needed */}
              {Array.from({ length: 2 - secondaryProducts.length }).map((_, index) => (
                <div
                  key={`placeholder-${index}`}
                  className="product-mini"
                  data-aos="zoom-in"
                  data-aos-delay={400 + (secondaryProducts.length + index) * 100}
                  style={{ cursor: 'pointer' }}
                  onClick={() => window.location.href = '/products'}
                >
                  <img src="/assets/img/product/placeholder.jpg" alt="Product" className="img-fluid" />
                  <span className="mini-price">View More</span>
                </div>
              ))}
            </div>
          </div>
          <div className="floating-elements">
            <div
              className="floating-icon cart"
              data-aos="fade-up"
              data-aos-delay="600"
              style={{ cursor: 'pointer' }}
              onClick={() => window.location.href = '/cart'}
            >
              <i className="bi bi-cart3"></i>
              <span className="notification-dot">0</span>
            </div>
            <div
              className="floating-icon wishlist"
              data-aos="fade-up"
              data-aos-delay="700"
              style={{ cursor: 'pointer' }}
              onClick={() => window.location.href = '/account?tab=wishlist'}
            >
              <i className="bi bi-heart"></i>
            </div>
            <div
              className="floating-icon search"
              data-aos="fade-up"
              data-aos-delay="800"
              style={{ cursor: 'pointer' }}
              onClick={toggleSearch}
            >
              <i className="bi bi-search"></i>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;