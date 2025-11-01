import React from 'react';
import { useProducts } from '../../hooks/useProducts';
import { useSettings } from '../../contexts/SettingsContext';
import { useCart } from '../../hooks/useCart';
import { Link } from 'react-router-dom';

const Hero = () => {
  const { products: featuredProducts, loading: productsLoading } = useProducts('featured');
  const { frontendSettings } = useSettings();
  const { cart, loading: cartLoading, addToCart } = useCart();

  const handleAddToCart = async (product) => {
    try {
      console.log('Adding product to cart:', product.id);
      await addToCart(product.id, 1);
      console.log('Product added to cart successfully:', product.name);
      alert(`${product.name} added to cart!`);
    } catch (error) {
      console.error('Failed to add to cart:', error);
      alert('Failed to add product to cart. Please try again.');
    }
  };

  const toggleSearch = () => {
    const searchInput = document.querySelector('.search-form input');
    if (searchInput) {
      searchInput.focus();
    }
  };

  // Calculate total items in cart
  const totalCartItems = cart?.total_items || cart?.items?.reduce((total, item) => total + (item.quantity || 0), 0) || 0;

  if (productsLoading) {
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
              <Link to="/products" className="btn-primary">Shop Now</Link>
              <Link to="/products?featured=true" className="btn-secondary">Featured Products</Link>
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
                  src={getImageUrl(mainProduct.main_image_url)}
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
                    disabled={mainProduct.stock_status !== 'in_stock' || cartLoading}
                  >
                    {cartLoading ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2"></span>
                        Adding...
                      </>
                    ) : (
                      <>
                        <i className="bi bi-cart-plus me-2"></i>
                        {mainProduct.stock_status === 'in_stock' ? 'Add to Cart' : 'Out of Stock'}
                      </>
                    )}
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
                  <Link to="/products" className="btn btn-dark">
                    <i className="bi bi-cart-plus me-2"></i>
                    Shop Now
                  </Link>
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
                    src={getImageUrl(product.main_image_url)}
                    alt={product.name}
                    className="img-fluid"
                    onError={(e) => {
                      e.target.src = '/assets/img/product/placeholder.jpg';
                    }}
                  />
                  <span className="mini-price">{frontendSettings.currency_symbol}{product.base_price}</span>
                </div>
              ))}
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
            <Link
              to="/cart"
              className="floating-icon cart position-relative"
              data-aos="fade-up"
              data-aos-delay="600"
            >
              <i className="bi bi-cart3"></i>
              {!cartLoading && totalCartItems > 0 && (
                <span className="notification-dot position-absolute top-0 start-100 translate-middle badge bg-primary rounded-pill">
                  {totalCartItems}
                </span>
              )}
            </Link>
            <Link
              to="/wishlist"
              className="floating-icon wishlist"
              data-aos="fade-up"
              data-aos-delay="700"
            >
              <i className="bi bi-heart"></i>
            </Link>
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