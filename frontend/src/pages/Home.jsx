import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useSiteSettings } from '../contexts/SiteSettingsContext'
import { useCart } from '../contexts/CartContext'
import { getFeaturedProducts, getProducts } from '../services/api'

const Home = () => {
  const { settings } = useSiteSettings()
  const { addToCart } = useCart()
  const [featuredProducts, setFeaturedProducts] = useState([])
  const [newArrivals, setNewArrivals] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch featured products
        const featured = await getFeaturedProducts()
        setFeaturedProducts(featured.products || [])

        // Fetch new arrivals
        const arrivals = await getProducts({ sort_by: 'created_at', sort_order: 'desc', page_size: 8 })
        setNewArrivals(arrivals.products || [])

        // Mock categories for now
        setCategories([
          { id: 1, name: 'Electronics', slug: 'electronics', image_url: '/static/img/categories/electronics.jpg' },
          { id: 2, name: 'Clothing', slug: 'clothing', image_url: '/static/img/categories/clothing.jpg' },
          { id: 3, name: 'Home & Kitchen', slug: 'home-kitchen', image_url: '/static/img/categories/home.jpg' },
          { id: 4, name: 'Beauty', slug: 'beauty', image_url: '/static/img/categories/beauty.jpg' }
        ])
      } catch (error) {
        console.error('Error fetching home data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const handleAddToCart = (product, e) => {
    e.preventDefault()
    e.stopPropagation()
    addToCart(product)
  }

  if (loading) {
    return (
      <div className="container text-center py-5">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    )
  }

  return (
    <>
      {/* Hero Section */}
      <section className="hero-section bg-primary text-white py-5">
        <div className="container">
          <div className="row align-items-center">
            <div className="col-lg-6">
              <div className="hero-content">
                <h1 className="display-4 fw-bold mb-4">Welcome to {settings.site_name}</h1>
                <p className="lead mb-4">
                  Discover our curated collection of premium products designed to enhance your lifestyle. 
                  From electronics to fashion, find everything you need with exclusive deals and fast shipping.
                </p>
                <div className="hero-actions">
                  <Link to="/products" className="btn btn-light btn-lg me-3">Shop Now</Link>
                  <Link to="/products?featured=true" className="btn btn-outline-light btn-lg">Featured Products</Link>
                </div>
                <div className="features-list mt-4">
                  <div className="feature-item d-inline-flex align-items-center me-4">
                    <i className="bi bi-truck me-2"></i>
                    <span>Free Shipping Over {settings.currency_symbol}{settings.free_shipping_min_amount || '999'}</span>
                  </div>
                  <div className="feature-item d-inline-flex align-items-center me-4">
                    <i className="bi bi-arrow-clockwise me-2"></i>
                    <span>30-Day Returns</span>
                  </div>
                  <div className="feature-item d-inline-flex align-items-center">
                    <i className="bi bi-shield-check me-2"></i>
                    <span>Secure Payment</span>
                  </div>
                </div>
              </div>
            </div>
            <div className="col-lg-6">
              <div className="hero-image text-center">
                <img 
                  src="/static/img/hero-banner.jpg" 
                  alt="Hero Banner" 
                  className="img-fluid rounded shadow"
                  style={{ maxHeight: '400px', objectFit: 'cover' }}
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Categories */}
      <section className="categories-section py-5">
        <div className="container">
          <div className="row mb-5">
            <div className="col-12 text-center">
              <h2 className="section-title">Shop by Category</h2>
              <p className="text-muted">Explore our wide range of product categories</p>
            </div>
          </div>
          <div className="row g-4">
            {categories.map(category => (
              <div key={category.id} className="col-lg-3 col-md-6">
                <Link to={`/products?category=${category.slug}`} className="text-decoration-none">
                  <div className="category-card card h-100 border-0 shadow-sm">
                    <img 
                      src={category.image_url} 
                      className="card-img-top" 
                      alt={category.name}
                      style={{ height: '200px', objectFit: 'cover' }}
                    />
                    <div className="card-body text-center">
                      <h5 className="card-title">{category.name}</h5>
                      <span className="text-muted">Shop Now →</span>
                    </div>
                  </div>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Products */}
      <section className="featured-products py-5 bg-light">
        <div className="container">
          <div className="row mb-5">
            <div className="col-12 text-center">
              <h2 className="section-title">Featured Products</h2>
              <p className="text-muted">Our most popular products loved by customers</p>
            </div>
          </div>
          <div className="row g-4">
            {featuredProducts.slice(0, 4).map(product => (
              <div key={product.id} className="col-lg-3 col-md-6">
                <div className="product-card card h-100 border-0 shadow-sm">
                  <Link to={`/product/${product.slug}`} className="text-decoration-none">
                    <img 
                      src={product.main_image_url || '/static/img/product/placeholder.jpg'} 
                      className="card-img-top" 
                      alt={product.name}
                      style={{ height: '200px', objectFit: 'cover' }}
                    />
                  </Link>
                  <div className="card-body">
                    <Link to={`/product/${product.slug}`} className="text-decoration-none text-dark">
                      <h6 className="card-title">{product.name}</h6>
                    </Link>
                    <div className="product-price mb-2">
                      <span className="fw-bold text-primary">{settings.currency_symbol}{product.base_price}</span>
                      {product.compare_price && product.compare_price > product.base_price && (
                        <span className="text-muted text-decoration-line-through ms-2">
                          {settings.currency_symbol}{product.compare_price}
                        </span>
                      )}
                    </div>
                    <button 
                      className="btn btn-primary w-100"
                      onClick={(e) => handleAddToCart(product, e)}
                    >
                      Add to Cart
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="text-center mt-4">
            <Link to="/products" className="btn btn-outline-primary">View All Products</Link>
          </div>
        </div>
      </section>

      {/* New Arrivals */}
      <section className="new-arrivals py-5">
        <div className="container">
          <div className="row mb-5">
            <div className="col-12 text-center">
              <h2 className="section-title">New Arrivals</h2>
              <p className="text-muted">Check out our latest products</p>
            </div>
          </div>
          <div className="row g-4">
            {newArrivals.slice(0, 4).map(product => (
              <div key={product.id} className="col-lg-3 col-md-6">
                <div className="product-card card h-100 border-0 shadow-sm">
                  <div className="position-relative">
                    <Link to={`/product/${product.slug}`} className="text-decoration-none">
                      <img 
                        src={product.main_image_url || '/static/img/product/placeholder.jpg'} 
                        className="card-img-top" 
                        alt={product.name}
                        style={{ height: '200px', objectFit: 'cover' }}
                      />
                    </Link>
                    <span className="badge bg-success position-absolute top-0 start-0 m-2">New</span>
                  </div>
                  <div className="card-body">
                    <Link to={`/product/${product.slug}`} className="text-decoration-none text-dark">
                      <h6 className="card-title">{product.name}</h6>
                    </Link>
                    <div className="product-price mb-2">
                      <span className="fw-bold text-primary">{settings.currency_symbol}{product.base_price}</span>
                    </div>
                    <button 
                      className="btn btn-outline-primary w-100"
                      onClick={(e) => handleAddToCart(product, e)}
                    >
                      Add to Cart
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section py-5 bg-dark text-white">
        <div className="container">
          <div className="row g-4 text-center">
            <div className="col-lg-3 col-md-6">
              <div className="feature-icon mb-3">
                <i className="bi bi-truck display-6 text-primary"></i>
              </div>
              <h4>Free Shipping</h4>
              <p className="text-light">Free shipping on orders over {settings.currency_symbol}{settings.free_shipping_min_amount || '999'}</p>
            </div>
            <div className="col-lg-3 col-md-6">
              <div className="feature-icon mb-3">
                <i className="bi bi-arrow-clockwise display-6 text-primary"></i>
              </div>
              <h4>Easy Returns</h4>
              <p className="text-light">30-day return policy for all products</p>
            </div>
            <div className="col-lg-3 col-md-6">
              <div className="feature-icon mb-3">
                <i className="bi bi-shield-check display-6 text-primary"></i>
              </div>
              <h4>Secure Payment</h4>
              <p className="text-light">Your payment information is safe with us</p>
            </div>
            <div className="col-lg-3 col-md-6">
              <div className="feature-icon mb-3">
                <i className="bi bi-headset display-6 text-primary"></i>
              </div>
              <h4>24/7 Support</h4>
              <p className="text-light">Round-the-clock customer support</p>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}

export default Home
