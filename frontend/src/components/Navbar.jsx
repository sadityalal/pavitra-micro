// frontend/src/components/Navbar.jsx
import React, { useState, useEffect } from 'react'
import { Navbar, Nav, Container, NavDropdown, Badge, Form, Button, Offcanvas } from 'react-bootstrap'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useCart } from '../contexts/CartContext'
import { API } from '../services/api'

const NavigationBar = () => {
  const { user, logout, isAuthenticated } = useAuth()
  const { cart } = useCart()
  const navigate = useNavigate()
  const location = useLocation()
  const [categories, setCategories] = useState([])
  const [featuredProducts, setFeaturedProducts] = useState([])
  const [newArrivals, setNewArrivals] = useState([])
  const [showMobileMenu, setShowMobileMenu] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    loadNavigationData()
  }, [])

  const loadNavigationData = async () => {
    try {
      const [categoriesResponse, featuredResponse, newArrivalsResponse] = await Promise.all([
        API.products.getCategories(),
        API.products.getFeatured(),
        API.products.getNewArrivals()
      ])

      setCategories(categoriesResponse.data?.categories || categoriesResponse.data || [])
      setFeaturedProducts(featuredResponse.data?.products || featuredResponse.data || [])
      setNewArrivals(newArrivalsResponse.data?.products || newArrivalsResponse.data || [])
    } catch (error) {
      console.error('Error loading navigation data:', error)
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/')
    setShowMobileMenu(false)
  }

  const handleSearch = (e) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/products?search=${encodeURIComponent(searchQuery)}`)
      setSearchQuery('')
    }
  }

  const isActivePath = (path) => {
    return location.pathname === path
  }

  return (
    <>
      {/* Top Bar - Using your existing CSS classes */}
      <div className="top-bar py-2">
        <div className="container-fluid container-xl">
          <div className="row align-items-center">
            <div className="col-lg-4 d-none d-lg-flex">
              <div className="top-bar-item">
                <i className="bi bi-telephone-fill me-2"></i>
                <span>Need help? Call us: </span>
                <a href="tel:+919711317009">+91-9711317009</a>
              </div>
            </div>

            <div className="col-lg-4 col-md-12 text-center">
              <div className="announcement-slider swiper init-swiper">
                <div className="swiper-wrapper">
                  <div className="swiper-slide">🚚 Free shipping on orders over ₹999</div>
                  <div className="swiper-slide">💰 10-day money back guarantee</div>
                  <div className="swiper-slide">🎁 20% off on your first order</div>
                </div>
              </div>
            </div>

            <div className="col-lg-4 d-none d-lg-block">
              <div className="d-flex justify-content-end">
                <div className="top-bar-item dropdown me-3">
                  <a href="#" className="dropdown-toggle" data-bs-toggle="dropdown">
                    <i className="bi bi-translate me-2"></i>EN
                  </a>
                  <ul className="dropdown-menu">
                    <li><a className="dropdown-item" href="#"><i className="bi bi-check2 me-2 selected-icon"></i>English</a></li>
                    <li><a className="dropdown-item" href="#">Hindi</a></li>
                  </ul>
                </div>
                <div className="top-bar-item dropdown">
                  <a href="#" className="dropdown-toggle" data-bs-toggle="dropdown">
                    <i className="bi bi-currency-rupee me-2"></i>INR
                  </a>
                  <ul className="dropdown-menu">
                    <li><a className="dropdown-item" href="#"><i className="bi bi-check2 me-2 selected-icon"></i>INR</a></li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Header */}
      <header className="header sticky-top">
        <div className="main-header">
          <div className="container-fluid container-xl">
            <div className="d-flex py-3 align-items-center justify-content-between">
              {/* Logo */}
              <Link to="/" className="logo d-flex align-items-center text-decoration-none">
                <h1 className="sitename">Pavitra Enterprises</h1>
              </Link>

              {/* Search Form */}
              <Form className="search-form desktop-search-form" onSubmit={handleSearch}>
                <div className="input-group">
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Search for products"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                  <button className="btn" type="submit">
                    <i className="bi bi-search"></i>
                  </button>
                </div>
              </Form>

              {/* Actions */}
              <div className="header-actions d-flex align-items-center justify-content-end">
                {/* Mobile Search Toggle */}
                <button className="header-action-btn mobile-search-toggle d-xl-none" type="button">
                  <i className="bi bi-search"></i>
                </button>

                {/* Account Dropdown */}
                <div className="dropdown account-dropdown">
                  <button className="header-action-btn" data-bs-toggle="dropdown">
                    <i className="bi bi-person"></i>
                  </button>
                  <div className="dropdown-menu dropdown-menu-end">
                    {isAuthenticated ? (
                      <>
                        <div className="dropdown-header">
                          <h6>Welcome, <span className="text-primary">{user?.first_name || user?.email?.split('@')[0]}</span></h6>
                          <p className="mb-0">Access account & manage orders</p>
                        </div>
                        <div className="dropdown-body">
                          <Link className="dropdown-item d-flex align-items-center" to="/profile">
                            <i className="bi bi-person-circle me-2"></i>
                            <span>My Account</span>
                          </Link>
                          <Link className="dropdown-item d-flex align-items-center" to="/orders">
                            <i className="bi bi-bag-check me-2"></i>
                            <span>My Orders</span>
                          </Link>
                          <Link className="dropdown-item d-flex align-items-center" to="/wishlist">
                            <i className="bi bi-heart me-2"></i>
                            <span>My Wishlist</span>
                          </Link>
                          <Link className="dropdown-item d-flex align-items-center" to="/profile?tab=addresses">
                            <i className="bi bi-geo-alt me-2"></i>
                            <span>My Addresses</span>
                          </Link>
                        </div>
                        <div className="dropdown-footer">
                          <button onClick={handleLogout} className="btn btn-outline-primary w-100 btn-sm">Logout</button>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="dropdown-header">
                          <h6>Welcome to <span className="text-primary">Pavitra Enterprises</span></h6>
                          <p className="mb-0">Access account & manage orders</p>
                        </div>
                        <div className="dropdown-footer">
                          <Link to="/login" className="btn btn-primary w-100 mb-2 btn-sm">Sign In</Link>
                          <Link to="/register" className="btn btn-outline-primary w-100 btn-sm">Register</Link>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {/* Wishlist */}
                <Link to="/wishlist" className="header-action-btn d-none d-md-block position-relative">
                  <i className="bi bi-heart"></i>
                  <span className="badge" id="wishlist-count">0</span>
                </Link>

                {/* Cart */}
                <Link to="/cart" className="header-action-btn position-relative">
                  <i className="bi bi-cart3"></i>
                  <span className="badge" id="cart-count">{cart.total_items || 0}</span>
                </Link>

                {/* Mobile Navigation Toggle */}
                <button
                  className="mobile-nav-toggle d-xl-none me-0"
                  onClick={() => setShowMobileMenu(true)}
                >
                  <i className="bi bi-list"></i>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="header-nav">
          <div className="container-fluid container-xl position-relative">
            <nav id="navmenu" className="navmenu">
              <ul>
                <li><Link to="/" className={isActivePath('/') ? 'active' : ''}>Home</Link></li>
                <li><Link to="/about" className={isActivePath('/about') ? 'active' : ''}>About</Link></li>

                {/* Products Mega Menu */}
                <li className="products-megamenu-1 dropdown">
                  <a href="#"><span>Shop</span> <i className="bi bi-chevron-down toggle-dropdown"></i></a>

                  {/* Desktop Mega Menu */}
                  <div className="desktop-megamenu dropdown-menu">
                    <div className="megamenu-tabs">
                      <ul className="nav nav-tabs" id="productMegaMenuTabs" role="tablist">
                        <li className="nav-item" role="presentation">
                          <button className="nav-link active" id="featured-tab" data-bs-toggle="tab" data-bs-target="#featured-content" type="button">Featured</button>
                        </li>
                        <li className="nav-item" role="presentation">
                          <button className="nav-link" id="new-tab" data-bs-toggle="tab" data-bs-target="#new-content" type="button">New Arrivals</button>
                        </li>
                        <li className="nav-item" role="presentation">
                          <button className="nav-link" id="categories-tab" data-bs-toggle="tab" data-bs-target="#categories-content" type="button">Categories</button>
                        </li>
                      </ul>
                    </div>

                    <div className="megamenu-content tab-content">
                      {/* Featured Tab */}
                      <div className="tab-pane fade show active" id="featured-content" role="tabpanel">
                        <div className="product-grid">
                          {featuredProducts.slice(0, 4).map(product => (
                            <div key={product.id} className="product-card">
                              <Link to={`/products/${product.id}`} className="product-image-link">
                                <div className="product-image">
                                  <img
                                    src={product.main_image_url || '/static/img/product/placeholder.jpg'}
                                    alt={product.name}
                                    loading="lazy"
                                  />
                                  {product.compare_price && product.compare_price > product.base_price && (
                                    <span className="badge-sale">
                                      -{Math.round(((product.compare_price - product.base_price) / product.compare_price) * 100)}%
                                    </span>
                                  )}
                                </div>
                              </Link>
                              <div className="product-info">
                                <h5><Link to={`/products/${product.id}`}>{product.name}</Link></h5>
                                <p className="price">
                                  {product.compare_price && product.compare_price > product.base_price && (
                                    <span className="original-price">₹{product.compare_price.toFixed(2)}</span>
                                  )}
                                  ₹{product.base_price.toFixed(2)}
                                </p>
                                <Link to={`/products/${product.id}`} className="btn-view">View Product</Link>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* New Arrivals Tab */}
                      <div className="tab-pane fade" id="new-content" role="tabpanel">
                        <div className="product-grid">
                          {newArrivals.slice(0, 4).map(product => (
                            <div key={product.id} className="product-card">
                              <Link to={`/products/${product.id}`} className="product-image-link">
                                <div className="product-image">
                                  <img
                                    src={product.main_image_url || '/static/img/product/placeholder.jpg'}
                                    alt={product.name}
                                    loading="lazy"
                                  />
                                  <span className="badge-new">New</span>
                                </div>
                              </Link>
                              <div className="product-info">
                                <h5><Link to={`/products/${product.id}`}>{product.name}</Link></h5>
                                <p className="price">₹{product.base_price.toFixed(2)}</p>
                                <Link to={`/products/${product.id}`} className="btn-view">View Product</Link>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Categories Tab */}
                      <div className="tab-pane fade" id="categories-content" role="tabpanel">
                        <div className="category-grid">
                          {categories.map(category => (
                            <div key={category.id} className="category-column">
                              <h4><Link to={`/products?category=${category.id}`}>{category.name}</Link></h4>
                              <ul>
                                {category.products?.slice(0, 5).map(product => (
                                  <li key={product.id}>
                                    <Link to={`/products/${product.id}`}>{product.name}</Link>
                                  </li>
                                ))}
                                <li>
                                  <Link to={`/products?category=${category.id}`} className="view-all">
                                    View all {category.name}
                                  </Link>
                                </li>
                              </ul>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </li>

                <li><Link to="/contact" className={isActivePath('/contact') ? 'active' : ''}>Contact</Link></li>
              </ul>
            </nav>
          </div>
        </div>
      </header>

      {/* Mobile Menu Offcanvas */}
      <Offcanvas show={showMobileMenu} onHide={() => setShowMobileMenu(false)} placement="end">
        <Offcanvas.Header closeButton>
          <Offcanvas.Title>Menu</Offcanvas.Title>
        </Offcanvas.Header>
        <Offcanvas.Body>
          <Nav className="flex-column">
            <Nav.Link as={Link} to="/" onClick={() => setShowMobileMenu(false)}>Home</Nav.Link>
            <Nav.Link as={Link} to="/about" onClick={() => setShowMobileMenu(false)}>About</Nav.Link>
            <Nav.Link as={Link} to="/products" onClick={() => setShowMobileMenu(false)}>Shop</Nav.Link>
            <Nav.Link as={Link} to="/contact" onClick={() => setShowMobileMenu(false)}>Contact</Nav.Link>
            {isAuthenticated && (
              <>
                <Nav.Link as={Link} to="/orders" onClick={() => setShowMobileMenu(false)}>Orders</Nav.Link>
                <Nav.Link as={Link} to="/wishlist" onClick={() => setShowMobileMenu(false)}>Wishlist</Nav.Link>
                <Nav.Link as={Link} to="/profile" onClick={() => setShowMobileMenu(false)}>Profile</Nav.Link>
              </>
            )}
          </Nav>
        </Offcanvas.Body>
      </Offcanvas>
    </>
  )
}

export default NavigationBar