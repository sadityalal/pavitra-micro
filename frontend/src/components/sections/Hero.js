import React from 'react';

const Hero = () => {
  return (
    <section id="hero" className="hero section">
      <div className="hero-container">
        <div className="hero-content">
          <div className="content-wrapper" data-aos="fade-up" data-aos-delay="100">
            <h1 className="hero-title">Discover Amazing Products</h1>
            <p className="hero-description">
              Explore our curated collection of premium items designed to enhance your lifestyle. 
              From fashion to tech, find everything you need with exclusive deals and fast shipping.
            </p>
            <div className="hero-actions" data-aos="fade-up" data-aos-delay="200">
              <a href="#products" className="btn-primary">Shop Now</a>
              <a href="#categories" className="btn-secondary">Browse Categories</a>
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
            <div className="product-card featured">
              <img src="assets/img/product/product-2.webp" alt="Featured Product" className="img-fluid" />
              <div className="product-badge">Best Seller</div>
              <div className="product-info">
                <h4>Premium Wireless Headphones</h4>
                <div className="price">
                  <span className="sale-price">$299</span>
                  <span className="original-price">$399</span>
                </div>
              </div>
            </div>

            <div className="product-grid">
              <div className="product-mini" data-aos="zoom-in" data-aos-delay="400">
                <img src="assets/img/product/product-3.webp" alt="Product" className="img-fluid" />
                <span className="mini-price">$89</span>
              </div>
              <div className="product-mini" data-aos="zoom-in" data-aos-delay="500">
                <img src="assets/img/product/product-5.webp" alt="Product" className="img-fluid" />
                <span className="mini-price">$149</span>
              </div>
            </div>
          </div>

          <div className="floating-elements">
            <div className="floating-icon cart" data-aos="fade-up" data-aos-delay="600">
              <i className="bi bi-cart3"></i>
              <span className="notification-dot">3</span>
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
