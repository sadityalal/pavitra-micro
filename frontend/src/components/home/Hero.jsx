import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getImageUrl } from '../../utils/imageHelper';

// Small helper to dynamically load a script and return a promise
const loadScript = (src) => new Promise((resolve, reject) => {
  if (document.querySelector(`script[src="${src}"]`)) return resolve();
  const s = document.createElement('script');
  s.src = src;
  s.async = true;
  s.onload = () => resolve();
  s.onerror = (e) => reject(e);
  document.body.appendChild(s);
});

const Hero = ({ featuredProducts = [], totalItems = 0, siteSettings = {}, isAuthenticated }) => {
  useEffect(() => {
    // Try to load AOS from public/static vendor (if it's present)
    const init = async () => {
      try {
        await loadScript('/static/vendor/aos/aos.js');
        if (window.AOS && typeof window.AOS.init === 'function') {
          window.AOS.init({ once: true });
        }
      } catch (e) {
        // silently ignore if vendor files are absent
        // console.debug('AOS not available', e);
      }
    };
    init();
  }, []);

  const first = featuredProducts[0];
  const second = featuredProducts[1];
  const third = featuredProducts[2];

  const formatPrice = (price) => `${siteSettings.currency_symbol || '₹'}${parseFloat(price || 0).toFixed(2)}`;

  // Get image URLs using the helper
  const firstImageUrl = first ? getImageUrl(first.main_image_url) : '/static/img/product/placeholder.jpg';
  const secondImageUrl = second ? getImageUrl(second.main_image_url) : '/static/img/product/placeholder.jpg';
  const thirdImageUrl = third ? getImageUrl(third.main_image_url) : '/static/img/product/placeholder.jpg';

  return (
    <section id="hero" className="hero section">
      <div className="hero-container">
        <div className="hero-content">
          <div className="content-wrapper" data-aos="fade-up" data-aos-delay="100">
            <h1 className="hero-title">Discover Amazing Products</h1>
            <p className="hero-description">Explore our curated collection of premium items designed to enhance your lifestyle. From fashion to tech, find everything you need with exclusive deals and fast shipping.</p>
            <div className="hero-actions" data-aos="fade-up" data-aos-delay="200">
              <Link to="/products" className="btn-primary">Shop Now</Link>
              <Link to="/products" className="btn-secondary">Browse Categories</Link>
            </div>
            <div className="features-list" data-aos="fade-up" data-aos-delay="300">
              <div className="feature-item">
                <i className="bi bi-truck"></i>
                <span>Free Shipping</span>
              </div>
              <div className="feature-item">
                <i className="bi bi-award"></i>
                <span>Quality Guarantee</span>
              </div>
              <div className="feature-item">
                <i className="bi bi-headset"></i>
                <span>24/7 Support</span>
              </div>
            </div>
          </div>
        </div>

        <div className="hero-visuals">
          <div className="product-showcase" data-aos="fade-left" data-aos-delay="200">
            {first ? (
              <div className="product-card featured">
                <img
                  src={firstImageUrl}
                  alt={first.name}
                  className="img-fluid"
                  onError={(e) => e.currentTarget.src = '/static/img/product/placeholder.jpg'}
                />
                <div className="product-badge">Best Seller</div>
                <div className="product-info">
                  <h4>{first.name}</h4>
                  <div className="price">
                    <span className="sale-price">{formatPrice(first.base_price)}</span>
                    {first.compare_price && first.compare_price > first.base_price && (
                      <span className="original-price">{formatPrice(first.compare_price)}</span>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="product-card featured placeholder">
                <img src={getImageUrl(null)} alt="placeholder" className="img-fluid" />
              </div>
            )}

            <div className="product-grid">
              {second && (
                <div className="product-mini" data-aos="zoom-in" data-aos-delay="400">
                  <img
                    src={secondImageUrl}
                    alt={second.name}
                    className="img-fluid"
                    onError={(e) => e.currentTarget.src = '/static/img/product/placeholder.jpg'}
                  />
                  <span className="mini-price">{formatPrice(second.base_price)}</span>
                </div>
              )}
              {third && (
                <div className="product-mini" data-aos="zoom-in" data-aos-delay="500">
                  <img
                    src={thirdImageUrl}
                    alt={third.name}
                    className="img-fluid"
                    onError={(e) => e.currentTarget.src = '/static/img/product/placeholder.jpg'}
                  />
                  <span className="mini-price">{formatPrice(third.base_price)}</span>
                </div>
              )}
            </div>
          </div>

          <div className="floating-elements">
            <div className="floating-icon cart" data-aos="fade-up" data-aos-delay="600">
              <i className="bi bi-cart3"></i>
              <span className="notification-dot">{totalItems}</span>
            </div>
            <div className="floating-icon wishlist" data-aos="fade-up" data-aos-delay="700">
              <i className="bi bi-heart"></i>
            </div>
            <div className="floating-icon search" data-aos="fade-up" data-aos-delay="800">
              <i className="bi bi-search"></i>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;