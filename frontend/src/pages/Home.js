// frontend/src/pages/Home.js
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
      <section className="hero-section bg-primary text-white py-5">
        <div className="container">
          <div className="row align-items-center">
            <div className="col-lg-6">
              <h1 className="display-4 fw-bold">Welcome to Pavitra Enterprises</h1>
              <p className="lead">Your trusted destination for quality products at great prices.</p>
              <div className="mt-4">
                <a href="/products" className="btn btn-light btn-lg me-3">Shop Now</a>
                <a href="/about" className="btn btn-outline-light btn-lg">Learn More</a>
              </div>
            </div>
            <div className="col-lg-6">
              <img 
                src="/static/img/hero-image.jpg" 
                alt="Hero" 
                className="img-fluid rounded"
                onError={(e) => {
                  e.target.src = 'https://via.placeholder.com/600x400/0d6efd/ffffff?text=Pavitra+Enterprises';
                }}
              />
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section py-5">
        <div className="container">
          <div className="row text-center">
            <div className="col-md-3">
              <div className="feature-item">
                <i className="bi bi-truck display-4 text-primary"></i>
                <h5>Free Shipping</h5>
                <p>Free shipping on orders over {formatPrice(siteSettings.free_shipping_threshold || 999)}</p>
              </div>
            </div>
            <div className="col-md-3">
              <div className="feature-item">
                <i className="bi bi-arrow-clockwise display-4 text-primary"></i>
                <h5>Easy Returns</h5>
                <p>{siteSettings.return_period_days || 10}-day return policy</p>
              </div>
            </div>
            <div className="col-md-3">
              <div className="feature-item">
                <i className="bi bi-shield-check display-4 text-primary"></i>
                <h5>Secure Payment</h5>
                <p>Your payment information is safe with us</p>
              </div>
            </div>
            <div className="col-md-3">
              <div className="feature-item">
                <i className="bi bi-headset display-4 text-primary"></i>
                <h5>24/7 Support</h5>
                <p>Round-the-clock customer support</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Products */}
      <section className="featured-products py-5 bg-light">
        <div className="container">
          <h2 className="text-center mb-5">Featured Products</h2>
          <div className="row">
            {featuredProducts.map(product => (
              <div className="col-lg-3 col-md-4 col-sm-6 mb-4" key={product.id}>
                <div className="card product-card h-100">
                  <img 
                    src={product.main_image_url || '/static/img/product-placeholder.jpg'} 
                    className="card-img-top" 
                    alt={product.name}
                    style={{ height: '200px', objectFit: 'cover' }}
                  />
                  <div className="card-body">
                    <h5 className="card-title">{product.name}</h5>
                    <p className="card-text text-muted">{product.short_description}</p>
                    <div className="d-flex justify-content-between align-items-center">
                      <span className="h5 text-primary mb-0">{formatPrice(product.base_price)}</span>
                      {product.compare_price && product.compare_price > product.base_price && (
                        <span className="text-muted text-decoration-line-through">
                          {formatPrice(product.compare_price)}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="card-footer bg-transparent">
                    <button 
                      className="btn btn-primary w-100"
                      onClick={() => handleAddToCart(product)}
                      disabled={product.stock_status !== 'in_stock'}
                    >
                      {product.stock_status === 'in_stock' ? 'Add to Cart' : 'Out of Stock'}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
          {featuredProducts.length === 0 && (
            <div className="text-center">
              <p className="text-muted">No featured products available at the moment.</p>
              <a href="/products" className="btn btn-primary">Browse All Products</a>
            </div>
          )}
        </div>
      </section>

      {/* Categories Section */}
      <section className="categories-section py-5">
        <div className="container">
          <h2 className="text-center mb-5">Shop by Category</h2>
          <div className="row">
            {categories.map(category => (
              <div className="col-lg-2 col-md-4 col-sm-6 mb-3" key={category.id}>
                <a href={`/categories/${category.slug}`} className="text-decoration-none">
                  <div className="category-card text-center">
                    <div className="category-image mb-3">
                      <img 
                        src={category.image_url || '/static/img/category-placeholder.jpg'} 
                        alt={category.name}
                        className="img-fluid rounded-circle"
                        style={{ width: '100px', height: '100px', objectFit: 'cover' }}
                      />
                    </div>
                    <h6 className="category-name">{category.name}</h6>
                  </div>
                </a>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;