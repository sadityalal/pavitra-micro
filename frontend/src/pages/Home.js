// frontend/src/pages/Home.js
import React, { useState, useEffect } from 'react';
import { productService } from '../services/productService';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import { Link } from 'react-router-dom';

const Home = () => {
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [newArrivals, setNewArrivals] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const { siteSettings, isAuthenticated } = useAuth();
  const { addToCart, totalItems } = useCart();

  useEffect(() => {
    loadHomeData();
  }, []);

  const loadHomeData = async () => {
    try {
      setLoading(true);
      const [featuredResponse, newArrivalsResponse, categoriesResponse] = await Promise.all([
        productService.getProducts({ featured: true, limit: 8 }),
        productService.getProducts({ new_arrivals: true, limit: 6 }),
        productService.getCategories()
      ]);

      setFeaturedProducts(featuredResponse.products || []);
      setNewArrivals(newArrivalsResponse.products || []);
      setCategories(categoriesResponse || []);
    } catch (error) {
      console.error('Failed to load home page data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async (product, event) => {
    if (event) event.stopPropagation();
    try {
      await addToCart(product.id, 1, product);
    } catch (error) {
      console.error('Failed to add product to cart:', error);
    }
  };

  const handleAddToWishlist = async (productId, event) => {
    if (event) event.stopPropagation();
    if (!isAuthenticated) {
      alert('Please login to add items to wishlist');
      return;
    }
    // Wishlist functionality would be implemented here
    console.log('Add to wishlist:', productId);
  };

  const formatPrice = (price) => {
    return `${siteSettings.currency_symbol || '₹'}${parseFloat(price).toFixed(2)}`;
  };

  if (loading) {
    return (
      <div className="container py-5 text-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <p className="mt-3">Loading amazing products...</p>
      </div>
    );
  }

  return (
    <div className="home-page">
      {/* Hero Section */}
      <section id="hero" className="hero section">
        <div className="hero-container">
          <div className="hero-content">
            <div className="content-wrapper" data-aos="fade-up" data-aos-delay="100">
              <h1 className="hero-title">Welcome to Pavitra Enterprises</h1>
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
                  <span>Free Shipping Over {formatPrice(siteSettings.free_shipping_threshold || 999)}</span>
                </div>
                <div className="feature-item">
                  <i className="bi bi-arrow-clockwise"></i>
                  <span>{siteSettings.return_period_days || 10}-Day Returns</span>
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
              {featuredProducts[0] && (
                <div
                  className="product-card featured"
                  style={{cursor: 'pointer'}}
                  onClick={() => window.location.href = `/products/${featuredProducts[0].slug || featuredProducts[0].id}`}
                >
                  <img
                    src={featuredProducts[0].main_image_url || '/static/img/product/placeholder.jpg'}
                    alt={featuredProducts[0].name}
                    className="img-fluid"
                  />
                  <div className="product-badge">Best Seller</div>
                  <div className="product-info">
                    <h4>
                      <Link to={`/products/${featuredProducts[0].slug || featuredProducts[0].id}`} onClick={e => e.stopPropagation()}>
                        {featuredProducts[0].name}
                      </Link>
                    </h4>
                    <div className="price">
                      <span className="sale-price">{formatPrice(featuredProducts[0].base_price)}</span>
                      {featuredProducts[0].compare_price && featuredProducts[0].compare_price > featuredProducts[0].base_price && (
                        <span className="original-price">{formatPrice(featuredProducts[0].compare_price)}</span>
                      )}
                    </div>
                  </div>
                </div>
              )}

              <div className="product-grid">
                {featuredProducts[1] && (
                  <div
                    className="product-mini"
                    data-aos="zoom-in"
                    data-aos-delay="400"
                    style={{cursor: 'pointer'}}
                    onClick={() => window.location.href = `/products/${featuredProducts[1].slug || featuredProducts[1].id}`}
                  >
                    <img
                      src={featuredProducts[1].main_image_url || '/static/img/product/placeholder.jpg'}
                      alt={featuredProducts[1].name}
                      className="img-fluid"
                    />
                    <span className="mini-price">{formatPrice(featuredProducts[1].base_price)}</span>
                  </div>
                )}
                {featuredProducts[2] && (
                  <div
                    className="product-mini"
                    data-aos="zoom-in"
                    data-aos-delay="500"
                    style={{cursor: 'pointer'}}
                    onClick={() => window.location.href = `/products/${featuredProducts[2].slug || featuredProducts[2].id}`}
                  >
                    <img
                      src={featuredProducts[2].main_image_url || '/static/img/product/placeholder.jpg'}
                      alt={featuredProducts[2].name}
                      className="img-fluid"
                    />
                    <span className="mini-price">{formatPrice(featuredProducts[2].base_price)}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="floating-elements">
              <div
                className="floating-icon cart"
                data-aos="fade-up"
                data-aos-delay="600"
                style={{cursor: 'pointer'}}
                onClick={() => window.location.href = '/cart'}
              >
                <i className="bi bi-cart3"></i>
                <span className="notification-dot">{totalItems}</span>
              </div>

              <div
                className="floating-icon wishlist"
                data-aos="fade-up"
                data-aos-delay="700"
                style={{cursor: 'pointer'}}
                onClick={() => window.location.href = isAuthenticated ? '/account?tab=wishlist' : '/login'}
              >
                <i className="bi bi-heart"></i>
              </div>

              <div
                className="floating-icon search"
                data-aos="fade-up"
                data-aos-delay="800"
                style={{cursor: 'pointer'}}
                onClick={() => document.querySelector('.search-form input')?.focus()}
              >
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
              {categories[0] && (
                <div className="category-featured" data-aos="fade-right" data-aos-delay="200">
                  <div
                    className="category-image"
                    style={{cursor: 'pointer'}}
                    onClick={() => window.location.href = `/categories/${categories[0].slug || categories[0].id}`}
                  >
                    <img
                      src={categories[0].image_url || '/static/img/categories/placeholder.jpg'}
                      alt={categories[0].name}
                      className="img-fluid"
                    />
                  </div>
                  <div className="category-content">
                    <span className="category-tag">Trending Now</span>
                    <h2>{categories[0].name} Collection</h2>
                    <p>{categories[0].description || 'Discover our latest arrivals designed for the modern lifestyle.'}</p>
                    <Link
                      to={`/categories/${categories[0].slug || categories[0].id}`}
                      className="btn-shop"
                    >
                      Explore Collection <i className="bi bi-arrow-right"></i>
                    </Link>
                  </div>
                </div>
              )}
            </div>

            <div className="col-lg-6">
              <div className="row gy-4">
                {categories.slice(1, 5).map((category, index) => (
                  <div className="col-xl-6" key={category.id}>
                    <div
                      className={`category-card cat-${category.slug}`}
                      data-aos="fade-up"
                      data-aos-delay={300 + index * 100}
                      style={{cursor: 'pointer'}}
                      onClick={() => window.location.href = `/categories/${category.slug || category.id}`}
                    >
                      <div className="category-image">
                        <img
                          src={category.image_url || '/static/img/categories/placeholder.jpg'}
                          alt={category.name}
                          className="img-fluid"
                        />
                      </div>
                      <div className="category-content">
                        <h4>{category.name}</h4>
                        <p>{category.product_count || 0} products</p>
                        <Link
                          to={`/categories/${category.slug || category.id}`}
                          className="card-link"
                          onClick={e => e.stopPropagation()}
                        >
                          Shop Now <i className="bi bi-arrow-right"></i>
                        </Link>
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
            {featuredProducts.slice(0, 4).map((product) => (
              <div className="col-lg-3 col-md-6" key={product.id}>
                <div
                  className="product-item"
                  style={{cursor: 'pointer'}}
                  onClick={() => window.location.href = `/products/${product.slug || product.id}`}
                >
                  <div className="product-image">
                    {product.compare_price && product.compare_price > product.base_price && (
                      <div className="product-badge sale-badge">
                        {Math.round((1 - product.base_price / product.compare_price) * 100)}% Off
                      </div>
                    )}
                    {product.is_featured && !product.compare_price && (
                      <div className="product-badge">Featured</div>
                    )}

                    <img
                      src={product.main_image_url || '/static/img/product/placeholder.jpg'}
                      alt={product.name}
                      className="img-fluid"
                      loading="lazy"
                    />

                    <div className="product-actions" onClick={e => e.stopPropagation()}>
                      <button
                        className="action-btn wishlist-btn"
                        onClick={(e) => handleAddToWishlist(product.id, e)}
                      >
                        <i className="bi bi-heart"></i>
                      </button>
                      <Link
                        to={`/products/${product.slug || product.id}`}
                        className="action-btn quickview-btn"
                      >
                        <i className="bi bi-eye"></i>
                      </Link>
                    </div>

                    {product.stock_quantity > 0 ? (
                      <button
                        className="cart-btn"
                        onClick={(e) => handleAddToCart(product, e)}
                      >
                        Add to Cart
                      </button>
                    ) : (
                      <button className="cart-btn" disabled>Out of Stock</button>
                    )}
                  </div>

                  <div className="product-info">
                    <div className="product-category">
                      {product.category_name || product.category?.name || 'Uncategorized'}
                    </div>
                    <h4 className="product-name">
                      <Link
                        to={`/products/${product.slug || product.id}`}
                        onClick={e => e.stopPropagation()}
                      >
                        {product.name}
                      </Link>
                    </h4>

                    <div className="product-rating">
                      <div className="stars">
                        {[...Array(5)].map((_, i) => (
                          <i
                            key={i}
                            className={`bi bi-star${i < (product.average_rating || 0) ? '-fill' : ''}`}
                          ></i>
                        ))}
                      </div>
                      <span className="rating-count">({product.review_count || 0})</span>
                    </div>

                    <div className="product-price">
                      {product.compare_price && product.compare_price > product.base_price && (
                        <span className="old-price">{formatPrice(product.compare_price)}</span>
                      )}
                      <span className="current-price">{formatPrice(product.base_price)}</span>
                    </div>

                    {product.stock_quantity > 0 && product.stock_quantity <= (product.low_stock_threshold || 5) && (
                      <div className="stock-info">
                        <small className="text-warning">Only {product.stock_quantity} left!</small>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="text-center mt-5" data-aos="fade-up" data-aos-delay="200">
            <Link to="/products" className="btn btn-outline-primary">View All Products</Link>
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
              <p className="text-muted">Free shipping on orders over {formatPrice(siteSettings.free_shipping_threshold || 999)}</p>
            </div>
            <div className="col-lg-3 col-md-6 text-center">
              <div className="feature-icon mb-3">
                <i className="bi bi-arrow-clockwise display-6 text-primary"></i>
              </div>
              <h4>Easy Returns</h4>
              <p className="text-muted">{siteSettings.return_period_days || 10}-day return policy</p>
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
    </div>
  );
};

export default Home;