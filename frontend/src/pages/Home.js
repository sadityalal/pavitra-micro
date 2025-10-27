import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

const Home = () => {
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHomeData();
  }, []);

  const loadHomeData = async () => {
    try {
      setLoading(true);
      
      // Load featured products
      const productsResponse = await api.getProducts({ 
        featured: true, 
        limit: 8 
      });
      setFeaturedProducts(productsResponse.products || []);
      
      // Load categories
      const categoriesResponse = await api.getCategories();
      setCategories(categoriesResponse || []);
      
    } catch (error) {
      console.error('Failed to load home data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="container py-5">
        <div className="text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Hero Section */}
      <section className="bg-primary text-white py-5">
        <div className="container">
          <div className="row align-items-center">
            <div className="col-lg-6">
              <h1 className="display-4 fw-bold mb-4">
                Welcome to Pavitra Trading
              </h1>
              <p className="lead mb-4">
                Your trusted destination for quality products at great prices. 
                Discover amazing deals and shop with confidence.
              </p>
              <Link to="/products" className="btn btn-light btn-lg">
                Shop Now
              </Link>
            </div>
            <div className="col-lg-6">
              <div className="text-center">
                <i className="bi bi-shop-window display-1 opacity-75"></i>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Categories Section */}
      <section className="py-5">
        <div className="container">
          <h2 className="text-center mb-5">Shop by Category</h2>
          <div className="row">
            {categories.slice(0, 6).map(category => (
              <div key={category.id} className="col-md-4 col-lg-2 mb-4">
                <Link 
                  to={`/products?category=${category.id}`} 
                  className="card text-decoration-none text-dark h-100 hover-shadow"
                >
                  <div className="card-body text-center">
                    {category.image_url ? (
                      <img 
                        src={category.image_url} 
                        alt={category.name}
                        className="img-fluid mb-3"
                        style={{ height: '80px', objectFit: 'cover' }}
                      />
                    ) : (
                      <i className="bi bi-grid-3x3-gap display-6 text-primary"></i>
                    )}
                    <h6 className="card-title">{category.name}</h6>
                  </div>
                </Link>
              </div>
            ))}
          </div>
          <div className="text-center mt-4">
            <Link to="/categories" className="btn btn-outline-primary">
              View All Categories
            </Link>
          </div>
        </div>
      </section>

      {/* Featured Products */}
      <section className="py-5 bg-light">
        <div className="container">
          <h2 className="text-center mb-5">Featured Products</h2>
          <div className="row">
            {featuredProducts.length > 0 ? (
              featuredProducts.map(product => (
                <div key={product.id} className="col-md-6 col-lg-3 mb-4">
                  <div className="card h-100 product-card">
                    {product.main_image_url && (
                      <img 
                        src={product.main_image_url} 
                        className="card-img-top"
                        alt={product.name}
                        style={{ height: '200px', objectFit: 'cover' }}
                      />
                    )}
                    <div className="card-body d-flex flex-column">
                      <h6 className="card-title">{product.name}</h6>
                      <p className="card-text text-muted small flex-grow-1">
                        {product.short_description || 'No description available'}
                      </p>
                      <div className="mt-auto">
                        <div className="d-flex justify-content-between align-items-center">
                          <span className="h6 text-primary mb-0">
                            {product.currency_symbol || '₹'}{product.base_price}
                          </span>
                          {product.compare_price && product.compare_price > product.base_price && (
                            <small className="text-muted text-decoration-line-through">
                              {product.currency_symbol || '₹'}{product.compare_price}
                            </small>
                          )}
                        </div>
                        <Link 
                          to={`/products/${product.slug || product.id}`}
                          className="btn btn-primary btn-sm w-100 mt-2"
                        >
                          View Details
                        </Link>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="col-12 text-center">
                <p className="text-muted">No featured products available at the moment.</p>
                <Link to="/products" className="btn btn-primary">
                  Browse All Products
                </Link>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-5">
        <div className="container">
          <div className="row text-center">
            <div className="col-md-4 mb-4">
              <div className="feature-icon bg-primary bg-gradient text-white rounded-circle mx-auto mb-3 p-3">
                <i className="bi bi-truck display-6"></i>
              </div>
              <h5>Free Shipping</h5>
              <p className="text-muted">
                Free shipping on orders over ₹500
              </p>
            </div>
            <div className="col-md-4 mb-4">
              <div className="feature-icon bg-success bg-gradient text-white rounded-circle mx-auto mb-3 p-3">
                <i className="bi bi-shield-check display-6"></i>
              </div>
              <h5>Secure Payment</h5>
              <p className="text-muted">
                100% secure payment processing
              </p>
            </div>
            <div className="col-md-4 mb-4">
              <div className="feature-icon bg-warning bg-gradient text-white rounded-circle mx-auto mb-3 p-3">
                <i className="bi bi-arrow-clockwise display-6"></i>
              </div>
              <h5>Easy Returns</h5>
              <p className="text-muted">
                10-day return policy
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;
