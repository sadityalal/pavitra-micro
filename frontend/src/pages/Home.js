import React from 'react';

const Home = () => {
  return (
    <>
      {/* Hero Section */}
      <section id="hero" className="hero section">
        <div className="hero-container">
          <div className="hero-content">
            <div className="content-wrapper" data-aos="fade-up" data-aos-delay="100">
              <h1 className="hero-title">Welcome to Pavitra Enterprises</h1>
              <p className="hero-description">Discover our curated collection of premium products designed to enhance your lifestyle. From electronics to fashion, find everything you need with exclusive deals and fast shipping.</p>
              <div className="hero-actions" data-aos="fade-up" data-aos-delay="200">
                <a href="/products" className="btn-primary">Shop Now</a>
                <a href="/products?featured=true" className="btn-secondary">Featured Products</a>
              </div>
              <div className="features-list" data-aos="fade-up" data-aos-delay="300">
                <div className="feature-item">
                  <i className="bi bi-truck"></i>
                  <span>Free Shipping Over ₹999</span>
                </div>
                <div className="feature-item">
                  <i className="bi bi-arrow-clockwise"></i>
                  <span>10-Day Returns</span>
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
              <div className="product-card featured" style={{cursor: 'pointer'}} onClick={() => window.location.href = '/products'}>
                <img src="/static/img/product/placeholder.jpg" alt="Featured Product" className="img-fluid" />
                <div className="product-badge">Coming Soon</div>
                <div className="product-info">
                  <h4>
                    <a href="/products" onClick={(e) => e.stopPropagation()}>New Arrivals Coming Soon</a>
                  </h4>
                  <div className="price">
                    <span className="sale-price">₹0.00</span>
                  </div>
                </div>
              </div>

              <div className="product-grid">
                <div className="product-mini" data-aos="zoom-in" data-aos-delay="400" style={{cursor: 'pointer'}} onClick={() => window.location.href = '/products'}>
                  <img src="/static/img/product/placeholder.jpg" alt="Product" className="img-fluid" />
                  <span className="mini-price">₹0.00</span>
                </div>
                <div className="product-mini" data-aos="zoom-in" data-aos-delay="500" style={{cursor: 'pointer'}} onClick={() => window.location.href = '/products'}>
                  <img src="/static/img/product/placeholder.jpg" alt="Product" className="img-fluid" />
                  <span className="mini-price">₹0.00</span>
                </div>
              </div>
            </div>

            <div className="floating-elements">
              <div className="floating-icon cart" data-aos="fade-up" data-aos-delay="600" style={{cursor: 'pointer'}} onClick={() => window.location.href = '/cart'}>
                <i className="bi bi-cart3"></i>
                <span className="notification-dot">0</span>
              </div>

              <div className="floating-icon wishlist" data-aos="fade-up" data-aos-delay="700" style={{cursor: 'pointer'}} onClick={() => window.location.href = '/account?tab=wishlist'}>
                <i className="bi bi-heart"></i>
              </div>

              <div className="floating-icon search" data-aos="fade-up" data-aos-delay="800" style={{cursor: 'pointer'}}>
                <i className="bi bi-search"></i>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Promo Cards Section */}
      <section id="promo-cards" className="promo-cards section">
        <div className="container" data-aos="fade-up" data-aos-delay="100">
          <div className="row gy-4">
            <div className="col-lg-6">
              <div className="category-featured" data-aos="fade-right" data-aos-delay="200">
                <div className="category-image" style={{cursor: 'pointer'}} onClick={() => window.location.href = '/products'}>
                  <img src="/static/img/categories/placeholder.jpg" alt="Categories" className="img-fluid" />
                </div>
                <div className="category-content">
                  <span className="category-tag">Coming Soon</span>
                  <h2>New Collections</h2>
                  <p>Exciting new categories coming soon to Pavitra Enterprises.</p>
                  <a href="/products" className="btn-shop">
                    Browse Products <i className="bi bi-arrow-right"></i>
                  </a>
                </div>
              </div>
            </div>

            <div className="col-lg-6">
              <div className="row gy-4">
                {[1, 2, 3, 4].map((i) => (
                  <div className="col-xl-6" key={i}>
                    <div className="category-card" data-aos="fade-up" data-aos-delay={300 + (i * 100)} style={{cursor: 'pointer'}} onClick={() => window.location.href = '/products'}>
                      <div className="category-image">
                        <img src="/static/img/categories/placeholder.jpg" alt={`Category ${i + 1}`} className="img-fluid" />
                      </div>
                      <div className="category-content">
                        <h4>Category {i + 1}</h4>
                        <p>0 products</p>
                        <a href="/products" className="card-link" onClick={(e) => e.stopPropagation()}>
                          Coming Soon <i className="bi bi-arrow-right"></i>
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Best Sellers Section */}
      <section id="best-sellers" className="best-sellers section">
        <div className="container section-title" data-aos="fade-up">
          <h2>Best Sellers</h2>
          <p>Our most popular products loved by customers</p>
        </div>

        <div className="container" data-aos="fade-up" data-aos-delay="100">
          <div className="row g-5">
            {[1, 2, 3, 4].map((i) => (
              <div className="col-lg-3 col-md-6" key={i}>
                <div className="product-item" style={{cursor: 'pointer'}} onClick={() => window.location.href = '/products'}>
                  <div className="product-image">
                    <img src="/static/img/product/placeholder.jpg" alt={`Product ${i}`} className="img-fluid" loading="lazy" />
                    <div className="product-actions" onClick={(e) => e.stopPropagation()}>
                      <a href="/products" className="action-btn quickview-btn">
                        <i className="bi bi-eye"></i>
                      </a>
                    </div>
                    <button className="cart-btn" onClick={(e) => { e.stopPropagation(); window.location.href = '/products'; }}>View Products</button>
                  </div>
                  <div className="product-info">
                    <div className="product-category">Coming Soon</div>
                    <h4 className="product-name">
                      <a href="/products" onClick={(e) => e.stopPropagation()}>Product {i}</a>
                    </h4>
                    <div className="product-rating">
                      <div className="stars">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <i key={star} className="bi bi-star"></i>
                        ))}
                      </div>
                      <span className="rating-count">(0)</span>
                    </div>
                    <div className="product-price">
                      <span className="current-price">₹0.00</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="text-center mt-5" data-aos="fade-up" data-aos-delay="200">
            <a href="/products" className="btn btn-outline-primary">View All Products</a>
          </div>
        </div>
      </section>

      {/* Cards Section */}
      <section id="cards" className="cards section">
        <div className="container" data-aos="fade-up" data-aos-delay="100">
          <div className="row gy-4">
            {/* Featured Items */}
            <div className="col-lg-4 col-md-6 mb-5 mb-md-0" data-aos="fade-up" data-aos-delay="200">
              <div className="product-category">
                <h3 className="category-title">
                  <i className="bi bi-star"></i> Featured Items
                </h3>
                <div className="product-list">
                  {[1, 2, 3].map((i) => (
                    <div className="product-card" key={i} style={{cursor: 'pointer'}} onClick={() => window.location.href = '/products'}>
                      <div className="product-image">
                        <img src="/static/img/product/placeholder.jpg" alt={`Product ${i}`} className="img-fluid" />
                      </div>
                      <div className="product-info">
                        <h4 className="product-name">
                          <a href="/products" onClick={(e) => e.stopPropagation()}>Featured Product {i}</a>
                        </h4>
                        <div className="product-rating">
                          <div className="stars">
                            {[1, 2, 3, 4, 5].map((star) => (
                              <i key={star} className="bi bi-star"></i>
                            ))}
                          </div>
                          <span>(0)</span>
                        </div>
                        <div className="product-price">
                          <span className="current-price">₹0.00</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Trending Now */}
            <div className="col-lg-4 col-md-6 mb-5 mb-md-0" data-aos="fade-up" data-aos-delay="300">
              <div className="product-category">
                <h3 className="category-title">
                  <i className="bi bi-fire"></i> Trending Now
                </h3>
                <div className="product-list">
                  {[1, 2, 3].map((i) => (
                    <div className="product-card" key={i} style={{cursor: 'pointer'}} onClick={() => window.location.href = '/products'}>
                      <div className="product-image">
                        <img src="/static/img/product/placeholder.jpg" alt={`Product ${i}`} className="img-fluid" />
                        <div className="product-badges">
                          <span className="badge-new">New</span>
                        </div>
                      </div>
                      <div className="product-info">
                        <h4 className="product-name">
                          <a href="/products" onClick={(e) => e.stopPropagation()}>New Arrival {i}</a>
                        </h4>
                        <div className="product-rating">
                          <div className="stars">
                            {[1, 2, 3, 4, 5].map((star) => (
                              <i key={star} className="bi bi-star"></i>
                            ))}
                          </div>
                          <span>(0)</span>
                        </div>
                        <div className="product-price">
                          <span className="current-price">₹0.00</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Best Sellers */}
            <div className="col-lg-4 col-md-6 mb-5 mb-md-0" data-aos="fade-up" data-aos-delay="400">
              <div className="product-category">
                <h3 className="category-title">
                  <i className="bi bi-award"></i> Best Sellers
                </h3>
                <div className="product-list">
                  {[1, 2, 3].map((i) => (
                    <div className="product-card" key={i} style={{cursor: 'pointer'}} onClick={() => window.location.href = '/products'}>
                      <div className="product-image">
                        <img src="/static/img/product/placeholder.jpg" alt={`Product ${i}`} className="img-fluid" />
                      </div>
                      <div className="product-info">
                        <h4 className="product-name">
                          <a href="/products" onClick={(e) => e.stopPropagation()}>Best Seller {i}</a>
                        </h4>
                        <div className="product-rating">
                          <div className="stars">
                            {[1, 2, 3, 4, 5].map((star) => (
                              <i key={star} className="bi bi-star"></i>
                            ))}
                          </div>
                          <span>(0)</span>
                        </div>
                        <div className="product-price">
                          <span className="current-price">₹0.00</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Call To Action Section */}
      <section id="call-to-action" className="call-to-action section">
        <div className="container" data-aos="fade-up" data-aos-delay="100">
          <div className="row">
            <div className="col-lg-8 mx-auto">
              <div className="main-content text-center" data-aos="zoom-in" data-aos-delay="200">
                <div className="offer-badge" data-aos="fade-down" data-aos-delay="250">
                  <span className="limited-time">Limited Time</span>
                  <span className="offer-text">50% OFF</span>
                </div>

                <h2 data-aos="fade-up" data-aos-delay="300">Exclusive Flash Sale</h2>

                <p className="subtitle" data-aos="fade-up" data-aos-delay="350">Don't miss out on our biggest sale of the year. Premium quality products at unbeatable prices for the next 48 hours only.</p>

                <div className="action-buttons" data-aos="fade-up" data-aos-delay="450">
                  <a href="/products" className="btn-shop-now">Shop Now</a>
                  <a href="/products" className="btn-view-deals">View All Deals</a>
                </div>
              </div>
            </div>
          </div>
          <div className="row featured-products-row" data-aos="fade-up" data-aos-delay="500">
            {[1, 2, 3, 4].map((i) => (
              <div className="col-lg-3 col-md-6" key={i} data-aos="zoom-in" data-aos-delay={100 + (i * 50)}>
                <div className="product-showcase" style={{cursor: 'pointer'}} onClick={() => window.location.href = '/products'}>
                  <div className="product-image">
                    <img src="/static/img/product/placeholder.jpg" alt={`Product ${i}`} className="img-fluid" />
                  </div>
                  <div className="product-details">
                    <h6>
                      <a href="/products" onClick={(e) => e.stopPropagation()}>Featured Product {i}</a>
                    </h6>
                    <div className="price-section">
                      <span className="sale-price">₹0.00</span>
                    </div>
                    <div className="rating-stars">
                      <div className="stars">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <i key={star} className="bi bi-star"></i>
                        ))}
                      </div>
                      <span className="rating-count">(0)</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="cards section">
        <div className="container" data-aos="fade-up" data-aos-delay="100">
          <div className="row g-4">
            <div className="col-lg-3 col-md-6 text-center">
              <div className="feature-icon mb-3">
                <i className="bi bi-truck display-6 text-primary"></i>
              </div>
              <h4>Free Shipping</h4>
              <p className="text-muted">Free shipping on orders over ₹999</p>
            </div>
            <div className="col-lg-3 col-md-6 text-center">
              <div className="feature-icon mb-3">
                <i className="bi bi-arrow-clockwise display-6 text-primary"></i>
              </div>
              <h4>Easy Returns</h4>
              <p className="text-muted">10-day return policy</p>
            </div>
            <div className="col-lg-3 col-md-6 text-center">
              <div className="feature-icon mb-3">
                <i className="bi bi-shield-check display-6 text-primary"></i>
              </div>
              <h4>Secure Payment</h4>
              <p className="text-muted">Your payment information is safe with us</p>
            </div>
            <div className="col-lg-3 col-md-6 text-center">
              <div className="feature-icon mb-3">
                <i className="bi bi-headset display-6 text-primary"></i>
              </div>
              <h4>24/7 Support</h4>
              <p className="text-muted">Round-the-clock customer support</p>
            </div>
          </div>
        </div>
      </section>
    </>
  );
};

export default Home;
