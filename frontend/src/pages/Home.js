import React, { useState, useEffect } from 'react';
import { productService } from '../services/productService';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';

const Home = () => {
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [newArrivals, setNewArrivals] = useState([]);
  const [bestSellers, setBestSellers] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const { siteSettings } = useAuth();
  const { addToCart } = useCart();

  useEffect(() => {
    loadHomeData();
  }, []);

  const loadHomeData = async () => {
    try {
      setLoading(true);
      
      // Load all data in parallel
      const [featuredResponse, newArrivalsResponse, bestSellersResponse, categoriesResponse] = await Promise.all([
        productService.getFeaturedProducts(8),
        productService.getNewArrivals(6),
        productService.getBestSellers(8),
        productService.getCategories()
      ]);

      setFeaturedProducts(featuredResponse.products || []);
      setNewArrivals(newArrivalsResponse.products || []);
      setBestSellers(bestSellersResponse.products || []);
      setCategories(categoriesResponse.categories || []);

    } catch (error) {
      console.error('Failed to load home page data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async (product) => {
    try {
      await addToCart(product.id, 1, product);
      // You can add a toast notification here
      console.log('Product added to cart:', product.name);
    } catch (error) {
      console.error('Failed to add product to cart:', error);
    }
  };

  const formatPrice = (price) => {
    return `${siteSettings.currency_symbol || '₹'}${parseFloat(price).toFixed(2)}`;
  };

  const getProductImage = (product) => {
    return product.main_image_url || '/static/img/product/placeholder.jpg';
  };

  const getCategoryImage = (category) => {
    return category.image_url || '/static/img/categories/placeholder.jpg';
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
    <>
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
                <a href="/products" className="btn-primary">Shop Now</a>
                <a href="/products?featured=true" className="btn-secondary">Featured Products</a>
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
              {featuredProducts[0] ? (
                <div className="product-card featured" onClick={() => window.location.href = `/products/${featuredProducts[0].slug}`}>
                  <img src={getProductImage(featuredProducts[0])} alt={featuredProducts[0].name} className="img-fluid" />
                  <div className="product-badge">Best Seller</div>
                  <div className="product-info">
                    <h4>{featuredProducts[0].name}</h4>
                    <div className="price">
                      <span className="sale-price">{formatPrice(featuredProducts[0].base_price)}</span>
                      {featuredProducts[0].compare_price && featuredProducts[0].compare_price > featuredProducts[0].base_price && (
                        <span className="original-price">{formatPrice(featuredProducts[0].compare_price)}</span>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="product-card featured" onClick={() => window.location.href = '/products'}>
                  <img src="/static/img/product/placeholder.jpg" alt="Featured Product" className="img-fluid" />
                  <div className="product-badge">Coming Soon</div>
                  <div className="product-info">
                    <h4>New Arrivals Coming Soon</h4>
                    <div className="price">
                      <span className="sale-price">{formatPrice(0)}</span>
                    </div>
                  </div>
                </div>
              )}

              <div className="product-grid">
                {featuredProducts[1] ? (
                  <div className="product-mini" data-aos="zoom-in" data-aos-delay="400" onClick={() => window.location.href = `/products/${featuredProducts[1].slug}`}>
                    <img src={getProductImage(featuredProducts[1])} alt={featuredProducts[1].name} className="img-fluid" />
                    <span className="mini-price">{formatPrice(featuredProducts[1].base_price)}</span>
                  </div>
                ) : (
                  <div className="product-mini" data-aos="zoom-in" data-aos-delay="400" onClick={() => window.location.href = '/products'}>
                    <img src="/static/img/product/placeholder.jpg" alt="Product" className="img-fluid" />
                    <span className="mini-price">{formatPrice(0)}</span>
                  </div>
                )}

                {featuredProducts[2] ? (
                  <div className="product-mini" data-aos="zoom-in" data-aos-delay="500" onClick={() => window.location.href = `/products/${featuredProducts[2].slug}`}>
                    <img src={getProductImage(featuredProducts[2])} alt={featuredProducts[2].name} className="img-fluid" />
                    <span className="mini-price">{formatPrice(featuredProducts[2].base_price)}</span>
                  </div>
                ) : (
                  <div className="product-mini" data-aos="zoom-in" data-aos-delay="500" onClick={() => window.location.href = '/products'}>
                    <img src="/static/img/product/placeholder.jpg" alt="Product" className="img-fluid" />
                    <span className="mini-price">{formatPrice(0)}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="floating-elements">
              <div className="floating-icon cart" data-aos="fade-up" data-aos-delay="600" onClick={() => window.location.href = '/cart'}>
                <i className="bi bi-cart3"></i>
                <span className="notification-dot">0</span>
              </div>

              <div className="floating-icon wishlist" data-aos="fade-up" data-aos-delay="700" onClick={() => window.location.href = '/account?tab=wishlist'}>
                <i className="bi bi-heart"></i>
              </div>

              <div className="floating-icon search" data-aos="fade-up" data-aos-delay="800" onClick={() => document.querySelector('.search-form input')?.focus()}>
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
                {categories[0] ? (
                  <>
                    <div className="category-image" onClick={() => window.location.href = `/categories/${categories[0].slug}`}>
                      <img src={getCategoryImage(categories[0])} alt={categories[0].name} className="img-fluid" />
                    </div>
                    <div className="category-content">
                      <span className="category-tag">Trending Now</span>
                      <h2>{categories[0].name} Collection</h2>
                      <p>{categories[0].description || 'Discover our latest arrivals designed for the modern lifestyle.'}</p>
                      <a href={`/categories/${categories[0].slug}`} className="btn-shop">
                        Explore Collection <i className="bi bi-arrow-right"></i>
                      </a>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="category-image" onClick={() => window.location.href = '/products'}>
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
                  </>
                )}
              </div>
            </div>

            <div className="col-lg-6">
              <div className="row gy-4">
                {categories.slice(1, 5).map((category, index) => (
                  <div className="col-xl-6" key={category.id}>
                    <div className="category-card" data-aos="fade-up" data-aos-delay={300 + (index * 100)} onClick={() => window.location.href = `/categories/${category.slug}`}>
                      <div className="category-image">
                        <img src={getCategoryImage(category)} alt={category.name} className="img-fluid" />
                      </div>
                      <div className="category-content">
                        <h4>{category.name}</h4>
                        <p>{category.product_count || 0} products</p>
                        <a href={`/categories/${category.slug}`} className="card-link" onClick={(e) => e.stopPropagation()}>
                          Shop Now <i className="bi bi-arrow-right"></i>
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
                
                {/* Fill remaining slots if fewer than 4 categories */}
                {categories.length < 5 && Array.from({ length: 4 - categories.slice(1).length }).map((_, index) => (
                  <div className="col-xl-6" key={`placeholder-${index}`}>
                    <div className="category-card" data-aos="fade-up" data-aos-delay={300 + ((categories.length + index) * 100)} onClick={() => window.location.href = '/products'}>
                      <div className="category-image">
                        <img src="/static/img/categories/placeholder.jpg" alt={`Category ${index + 2}`} className="img-fluid" />
                      </div>
                      <div className="category-content">
                        <h4>Category {categories.length + index + 1}</h4>
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
            {bestSellers.slice(0, 4).map((product) => (
              <div className="col-lg-3 col-md-6" key={product.id}>
                <div className="product-item">
                  <div className="product-image">
                    {product.compare_price && product.compare_price > product.base_price && (
                      <div className="product-badge sale-badge">
                        -{Math.round((1 - product.base_price / product.compare_price) * 100)}%
                      </div>
                    )}
                    {product.is_featured && !product.compare_price && (
                      <div className="product-badge">Featured</div>
                    )}

                    <img src={getProductImage(product)} alt={product.name} className="img-fluid" loading="lazy" 
                         onClick={() => window.location.href = `/products/${product.slug}`} />

                    <div className="product-actions">
                      <button className="action-btn wishlist-btn" onClick={(e) => {
                        e.stopPropagation();
                        // Add to wishlist functionality here
                        console.log('Add to wishlist:', product.id);
                      }}>
                        <i className="bi bi-heart"></i>
                      </button>
                      <button className="action-btn quickview-btn" onClick={(e) => {
                        e.stopPropagation();
                        window.location.href = `/products/${product.slug}`;
                      }}>
                        <i className="bi bi-eye"></i>
                      </button>
                    </div>

                    {product.stock_status === 'in_stock' ? (
                      <button className="cart-btn" onClick={(e) => {
                        e.stopPropagation();
                        handleAddToCart(product);
                      }}>
                        Add to Cart
                      </button>
                    ) : (
                      <button className="cart-btn" disabled>Out of Stock</button>
                    )}
                  </div>

                  <div className="product-info">
                    <div className="product-category">{product.category?.name || 'Uncategorized'}</div>
                    <h4 className="product-name">
                      <a href={`/products/${product.slug}`}>{product.name}</a>
                    </h4>

                    <div className="product-rating">
                      <div className="stars">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <i key={star} className={`bi bi-star${star <= (product.average_rating || 0) ? '-fill' : ''}`}></i>
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

                    {product.stock_quantity <= product.low_stock_threshold && product.stock_quantity > 0 && (
                      <div className="stock-info">
                        <small className="text-warning">Only {product.stock_quantity} left!</small>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {/* Show placeholder if no best sellers */}
            {bestSellers.length === 0 && Array.from({ length: 4 }).map((_, index) => (
              <div className="col-lg-3 col-md-6" key={`placeholder-${index}`}>
                <div className="product-item" onClick={() => window.location.href = '/products'}>
                  <div className="product-image">
                    <img src="/static/img/product/placeholder.jpg" alt={`Product ${index + 1}`} className="img-fluid" loading="lazy" />
                    <div className="product-actions">
                      <a href="/products" className="action-btn quickview-btn" onClick={(e) => e.stopPropagation()}>
                        <i className="bi bi-eye"></i>
                      </a>
                    </div>
                    <button className="cart-btn" onClick={(e) => {
                      e.stopPropagation();
                      window.location.href = '/products';
                    }}>
                      View Products
                    </button>
                  </div>
                  <div className="product-info">
                    <div className="product-category">Coming Soon</div>
                    <h4 className="product-name">
                      <a href="/products" onClick={(e) => e.stopPropagation()}>Product {index + 1}</a>
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
                      <span className="current-price">{formatPrice(0)}</span>
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

                <p className="subtitle" data-aos="fade-up" data-aos-delay="350">
                  Don't miss out on our biggest sale of the year. Premium quality products at unbeatable prices for the next 48 hours only.
                </p>

                <div className="action-buttons" data-aos="fade-up" data-aos-delay="450">
                  <a href="/products" className="btn-shop-now">Shop Now</a>
                  <a href="/products?on_sale=true" className="btn-view-deals">View All Deals</a>
                </div>
              </div>
            </div>
          </div>
          
          <div className="row featured-products-row" data-aos="fade-up" data-aos-delay="500">
            {featuredProducts.slice(0, 4).map((product, index) => (
              <div className="col-lg-3 col-md-6" key={product.id} data-aos="zoom-in" data-aos-delay={100 + (index * 50)}>
                <div className="product-showcase" onClick={() => window.location.href = `/products/${product.slug}`}>
                  <div className="product-image">
                    <img src={getProductImage(product)} alt={product.name} className="img-fluid" />
                    {product.compare_price && product.compare_price > product.base_price && (
                      <div className="discount-badge">
                        -{Math.round((1 - product.base_price / product.compare_price) * 100)}%
                      </div>
                    )}
                  </div>
                  <div className="product-details">
                    <h6>
                      <a href={`/products/${product.slug}`} onClick={(e) => e.stopPropagation()}>
                        {product.name}
                      </a>
                    </h6>
                    <div className="price-section">
                      {product.compare_price && product.compare_price > product.base_price && (
                        <span className="original-price">{formatPrice(product.compare_price)}</span>
                      )}
                      <span className="sale-price">{formatPrice(product.base_price)}</span>
                    </div>
                    <div className="rating-stars">
                      <div className="stars">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <i key={star} className={`bi bi-star${star <= (product.average_rating || 0) ? '-fill' : ''}`}></i>
                        ))}
                      </div>
                      <span className="rating-count">({product.review_count || 0})</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
            
            {/* Fill remaining slots if fewer than 4 featured products */}
            {featuredProducts.length < 4 && Array.from({ length: 4 - featuredProducts.length }).map((_, index) => (
              <div className="col-lg-3 col-md-6" key={`placeholder-${index}`} data-aos="zoom-in" data-aos-delay={100 + ((featuredProducts.length + index) * 50)}>
                <div className="product-showcase" onClick={() => window.location.href = '/products'}>
                  <div className="product-image">
                    <img src="/static/img/product/placeholder.jpg" alt={`Product ${index + 1}`} className="img-fluid" />
                  </div>
                  <div className="product-details">
                    <h6>
                      <a href="/products" onClick={(e) => e.stopPropagation()}>
                        Featured Product {featuredProducts.length + index + 1}
                      </a>
                    </h6>
                    <div className="price-section">
                      <span className="sale-price">{formatPrice(0)}</span>
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
    </>
  );
};

export default Home;
