// frontend/src/pages/Home.jsx
import React, { useState, useEffect } from 'react'
import { Container, Row, Col, Card, Button, Carousel } from 'react-bootstrap'
import { Link } from 'react-router-dom'
import { API } from '../services/api'
import ProductCard from '../components/products/ProductCard'
import LoadingSpinner from '../components/common/LoadingSpinner'

const Home = () => {
  const [featuredProducts, setFeaturedProducts] = useState([])
  const [bestsellers, setBestsellers] = useState([])
  const [newArrivals, setNewArrivals] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadHomeData()
  }, [])

  const loadHomeData = async () => {
    try {
      const [featuredResponse, bestsellersResponse, newArrivalsResponse, categoriesResponse] = await Promise.all([
        API.products.getFeatured(),
        API.products.getBestsellers(),
        API.products.getNewArrivals(),
        API.products.getCategories()
      ])

      setFeaturedProducts(featuredResponse.data?.products || featuredResponse.data || [])
      setBestsellers(bestsellersResponse.data?.products || bestsellersResponse.data || [])
      setNewArrivals(newArrivalsResponse.data?.products || newArrivalsResponse.data || [])
      setCategories(categoriesResponse.data?.categories || categoriesResponse.data || [])
    } catch (error) {
      console.error('Error loading home data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <LoadingSpinner text="Loading..." />
  }

  return (
    <main className="main">
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
              {featuredProducts[0] && (
                <div className="product-card featured" onClick={() => window.location.href = `/products/${featuredProducts[0].id}`}>
                  <img
                    src={featuredProducts[0].main_image_url || '/static/img/product/placeholder.jpg'}
                    alt={featuredProducts[0].name}
                    className="img-fluid"
                  />
                  <div className="product-badge">Best Seller</div>
                  <div className="product-info">
                    <h4>
                      <Link to={`/products/${featuredProducts[0].id}`}>{featuredProducts[0].name}</Link>
                    </h4>
                    <div className="price">
                      <span className="sale-price">₹{featuredProducts[0].base_price.toFixed(2)}</span>
                      {featuredProducts[0].compare_price && featuredProducts[0].compare_price > featuredProducts[0].base_price && (
                        <span className="original-price">₹{featuredProducts[0].compare_price.toFixed(2)}</span>
                      )}
                    </div>
                  </div>
                </div>
              )}

              <div className="product-grid">
                {featuredProducts[1] && (
                  <div className="product-mini" data-aos="zoom-in" data-aos-delay="400"
                       onClick={() => window.location.href = `/products/${featuredProducts[1].id}`}>
                    <img
                      src={featuredProducts[1].main_image_url || '/static/img/product/placeholder.jpg'}
                      alt={featuredProducts[1].name}
                      className="img-fluid"
                    />
                    <span className="mini-price">₹{featuredProducts[1].base_price.toFixed(2)}</span>
                  </div>
                )}
                {featuredProducts[2] && (
                  <div className="product-mini" data-aos="zoom-in" data-aos-delay="500"
                       onClick={() => window.location.href = `/products/${featuredProducts[2].id}`}>
                    <img
                      src={featuredProducts[2].main_image_url || '/static/img/product/placeholder.jpg'}
                      alt={featuredProducts[2].name}
                      className="img-fluid"
                    />
                    <span className="mini-price">₹{featuredProducts[2].base_price.toFixed(2)}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Promo Cards Section */}
      <section id="promo-cards" className="promo-cards section">
        <Container data-aos="fade-up" data-aos-delay="100">
          <Row className="gy-4">
            <Col lg={6}>
              <div className="category-featured" data-aos="fade-right" data-aos-delay="200">
                {categories[0] && (
                  <>
                    <div className="category-image" onClick={() => window.location.href = `/products?category=${categories[0].id}`}>
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
                      <Link to={`/products?category=${categories[0].id}`} className="btn-shop">
                        Explore Collection <i className="bi bi-arrow-right"></i>
                      </Link>
                    </div>
                  </>
                )}
              </div>
            </Col>
            <Col lg={6}>
              <Row className="gy-4">
                {categories.slice(1, 5).map((category, index) => (
                  <Col xl={6} key={category.id}>
                    <div className="category-card" data-aos="fade-up" data-aos-delay={300 + index * 100}
                         onClick={() => window.location.href = `/products?category=${category.id}`}>
                      <div className="category-image">
                        <img
                          src={category.image_url || '/static/img/categories/placeholder.jpg'}
                          alt={category.name}
                          className="img-fluid"
                        />
                      </div>
                      <div className="category-content">
                        <h4>{category.name}</h4>
                        <p>{category.products?.length || 0} products</p>
                        <Link to={`/products?category=${category.id}`} className="card-link" onClick={(e) => e.stopPropagation()}>
                          Shop Now <i className="bi bi-arrow-right"></i>
                        </Link>
                      </div>
                    </div>
                  </Col>
                ))}
              </Row>
            </Col>
          </Row>
        </Container>
      </section>

      {/* Best Sellers Section */}
      <section id="best-sellers" className="best-sellers section">
        <Container>
          <div className="section-title" data-aos="fade-up">
            <h2>Best Sellers</h2>
            <p>Our most popular products loved by customers</p>
          </div>

          <Row className="g-5" data-aos="fade-up" data-aos-delay="100">
            {featuredProducts.slice(0, 4).map(product => (
              <Col lg={3} md={6} key={product.id}>
                <ProductCard product={product} />
              </Col>
            ))}
          </Row>

          <div className="text-center mt-5" data-aos="fade-up" data-aos-delay="200">
            <Link to="/products" className="btn btn-outline-primary">View All Products</Link>
          </div>
        </Container>
      </section>

      {/* Features Section */}
      <section id="features" className="cards section">
        <Container data-aos="fade-up" data-aos-delay="100">
          <Row className="g-4">
            <Col lg={3} md={6} className="text-center">
              <div className="feature-icon mb-3">
                <i className="bi bi-truck display-6 text-primary"></i>
              </div>
              <h4>Free Shipping</h4>
              <p className="text-muted">Free shipping on orders over ₹999</p>
            </Col>
            <Col lg={3} md={6} className="text-center">
              <div className="feature-icon mb-3">
                <i className="bi bi-arrow-clockwise display-6 text-primary"></i>
              </div>
              <h4>Easy Returns</h4>
              <p className="text-muted">10-day return policy</p>
            </Col>
            <Col lg={3} md={6} className="text-center">
              <div className="feature-icon mb-3">
                <i className="bi bi-shield-check display-6 text-primary"></i>
              </div>
              <h4>Secure Payment</h4>
              <p className="text-muted">Your payment information is safe with us</p>
            </Col>
            <Col lg={3} md={6} className="text-center">
              <div className="feature-icon mb-3">
                <i className="bi bi-headset display-6 text-primary"></i>
              </div>
              <h4>24/7 Support</h4>
              <p className="text-muted">Round-the-clock customer support</p>
            </Col>
          </Row>
        </Container>
      </section>
    </main>
  )
}

export default Home