import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import axios from 'axios';

const BaseLayout = ({ children, user, setUser, title = 'Pavitra Enterprises', description = 'Premium Shopping Experience' }) => {
  const [cartCount, setCartCount] = useState(0);
  const [wishlistCount, setWishlistCount] = useState(0);
  const [categories, setCategories] = useState([]);
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [showMegaMenu, setShowMegaMenu] = useState(false);
  const [activeTab, setActiveTab] = useState('featured');
  const location = useLocation();

  useEffect(() => {
    document.title = title;
    fetchCartCount();
    fetchWishlistCount();
    fetchCategories();
    fetchFeaturedProducts();
  }, [user, title]);

  const fetchCartCount = async () => {
    if (user) {
      try {
        const response = await axios.get('http://localhost:8004/api/v1/users/cart', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setCartCount(response.data.total_items || 0);
      } catch (error) {
        console.error('Failed to fetch cart count:', error);
      }
    }
  };

  const fetchWishlistCount = async () => {
    if (user) {
      try {
        const response = await axios.get('http://localhost:8004/api/v1/users/wishlist', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setWishlistCount(response.data.total_count || 0);
      } catch (error) {
        console.error('Failed to fetch wishlist count:', error);
      }
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await axios.get('http://localhost:8002/api/v1/products/categories');
      setCategories(response.data || []);
    } catch (error) {
      console.error('Failed to fetch categories:', error);
    }
  };

  const fetchFeaturedProducts = async () => {
    try {
      const response = await axios.get('http://localhost:8002/api/v1/products/featured-products?page_size=4');
      setFeaturedProducts(response.data.products || []);
    } catch (error) {
      console.error('Failed to fetch featured products:', error);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  const isActive = (path) => {
    return location.pathname === path ? 'active' : '';
  };

  return (
    <div className="index-page">
      <header id="header" className="header sticky-top">
        {/* Top Bar */}
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
        <div className="main-header">
          <div className="container-fluid container-xl">
            <div className="d-flex py-3 align-items-center justify-content-between">
              {/* Logo */}
              <Link to="/" className="logo d-flex align-items-center text-decoration-none">
                <h1 className="sitename">Pavitra Enterprises</h1>
              </Link>

              {/* Search Form */}
              <form className="search-form desktop-search-form" action="/search" method="GET">
                <div className="input-group">
                  <input type="text" className="form-control" name="q" placeholder="Search for products" />
                  <button className="btn" type="submit">
                    <i className="bi bi-search"></i>
                  </button>
                </div>
              </form>

              {/* Actions */}
              <div className="header-actions d-flex align-items-center justify-content-end">
                {/* Account Dropdown */}
                <div className="dropdown account-dropdown">
                  <button className="header-action-btn" data-bs-toggle="dropdown">
                    <i className="bi bi-person"></i>
                  </button>
                  <div className="dropdown-menu dropdown-menu-end">
                    {user ? (
                      <>
                        <div className="dropdown-header">
                          <h6>Welcome, <span className="text-primary">{user.first_name}</span></h6>
                          <p className="mb-0">Access account & manage orders</p>
                        </div>
                        <div className="dropdown-body">
                          <Link className="dropdown-item d-flex align-items-center" to="/account/orders">
                            <i className="bi bi-person-circle me-2"></i>
                            <span>My Account</span>
                          </Link>
                          <Link className="dropdown-item d-flex align-items-center" to="/account/orders">
                            <i className="bi bi-bag-check me-2"></i>
                            <span>My Orders</span>
                          </Link>
                          <Link className="dropdown-item d-flex align-items-center" to="/account/wishlist">
                            <i className="bi bi-heart me-2"></i>
                            <span>My Wishlist</span>
                          </Link>
                          <Link className="dropdown-item d-flex align-items-center" to="/account/addresses">
                            <i className="bi bi-geo-alt me-2"></i>
                            <span>My Addresses</span>
                          </Link>
                        </div>
                        <div className="dropdown-footer">
                          <button onClick={logout} className="btn btn-outline-primary w-100 btn-sm">Logout</button>
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
                <Link to="/account/wishlist" className="header-action-btn d-none d-md-block position-relative">
                  <i className="bi bi-heart"></i>
                  <span className="badge" id="wishlist-count">{wishlistCount}</span>
                </Link>

                {/* Cart */}
                <Link to="/cart" className="header-action-btn position-relative">
                  <i className="bi bi-cart3"></i>
                  <span className="badge" id="cart-count">{cartCount}</span>
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="header-nav">
          <div className="container-fluid container-xl position-relative">
            <nav id="navmenu" className="navmenu">
              <ul>
                <li><Link to="/" className={isActive('/')}>Home</Link></li>
                <li><Link to="/about" className={isActive('/about')}>About</Link></li>

                {/* Products Mega Menu */}
                <li className="products-megamenu-1" 
                    onMouseEnter={() => setShowMegaMenu(true)}
                    onMouseLeave={() => setShowMegaMenu(false)}>
                  <a href="#"><span>Shop</span> <i className="bi bi-chevron-down toggle-dropdown"></i></a>

                  {showMegaMenu && (
                    <div className="desktop-megamenu">
                      <div className="megamenu-tabs">
                        <ul className="nav nav-tabs" id="productMegaMenuTabs" role="tablist">
                          <li className="nav-item" role="presentation">
                            <button 
                              className={`nav-link ${activeTab === 'featured' ? 'active' : ''}`}
                              onClick={() => setActiveTab('featured')}
                            >
                              Featured
                            </button>
                          </li>
                          <li className="nav-item" role="presentation">
                            <button 
                              className={`nav-link ${activeTab === 'new' ? 'active' : ''}`}
                              onClick={() => setActiveTab('new')}
                            >
                              New Arrivals
                            </button>
                          </li>
                          <li className="nav-item" role="presentation">
                            <button 
                              className={`nav-link ${activeTab === 'categories' ? 'active' : ''}`}
                              onClick={() => setActiveTab('categories')}
                            >
                              Categories
                            </button>
                          </li>
                        </ul>
                      </div>

                      <div className="megamenu-content tab-content">
                        {/* Featured Tab */}
                        {activeTab === 'featured' && (
                          <div className="tab-pane fade show active">
                            <div className="product-grid">
                              {featuredProducts.map(product => (
                                <div key={product.id} className="product-card">
                                  <Link to={`/product/${product.slug}`} className="product-image-link">
                                    <div className="product-image">
                                      <img 
                                        src={product.main_image_url || '/static/img/product/placeholder.jpg'} 
                                        alt={product.name} 
                                        loading="lazy" 
                                      />
                                      {product.compare_price && product.compare_price > product.base_price && (
                                        <span className="badge-sale">
                                          -{Math.round((product.compare_price - product.base_price) / product.compare_price * 100)}%
                                        </span>
                                      )}
                                    </div>
                                  </Link>
                                  <div className="product-info">
                                    <h5><Link to={`/product/${product.slug}`}>{product.name}</Link></h5>
                                    <p className="price">
                                      {product.compare_price && product.compare_price > product.base_price && (
                                        <span className="original-price">₹{product.compare_price.toFixed(2)}</span>
                                      )}
                                      ₹{product.base_price.toFixed(2)}
                                    </p>
                                    <Link to={`/product/${product.slug}`} className="btn-view">View Product</Link>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Categories Tab */}
                        {activeTab === 'categories' && (
                          <div className="tab-pane fade show active">
                            <div className="category-grid">
                              {categories.map(category => (
                                <div key={category.id} className="category-column">
                                  <h4><Link to={`/category/${category.slug}`}>{category.name}</Link></h4>
                                  <ul>
                                    <li><Link to={`/category/${category.slug}`} className="view-all">View all {category.name}</Link></li>
                                  </ul>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </li>

                <li><Link to="/contact" className={isActive('/contact')}>Contact</Link></li>
              </ul>
            </nav>
          </div>
        </div>
      </header>

      <main className="main">
        {/* Flash Messages Area */}
        <div className="container mt-3" id="flash-messages"></div>
        
        {/* Page Content */}
        {children}
      </main>

      <footer id="footer" className="footer dark-background">
        {/* Footer content from your template */}
        <div className="footer-main">
          <div className="container">
            <div className="row gy-4">
              <div className="col-lg-4 col-md-6">
                <div className="footer-widget footer-about">
                  <Link to="/" className="logo text-decoration-none">
                    <span className="sitename">Pavitra Enterprises</span>
                  </Link>
                  <p>Your trusted destination for quality products at great prices. We offer a wide range of electronics, clothing, home goods and more with excellent customer service.</p>

                  <div className="social-links mt-4">
                    <h5>Connect With Us</h5>
                    <div className="social-icons">
                      <a href="#" aria-label="Facebook"><i className="bi bi-facebook"></i></a>
                      <a href="#" aria-label="Instagram"><i className="bi bi-instagram"></i></a>
                      <a href="#" aria-label="Twitter"><i className="bi bi-twitter-x"></i></a>
                      <a href="#" aria-label="YouTube"><i className="bi bi-youtube"></i></a>
                    </div>
                  </div>
                </div>
              </div>

              <div className="col-lg-2 col-md-6 col-sm-6">
                <div className="footer-widget">
                  <h4>Shop</h4>
                  <ul className="footer-links">
                    <li><Link to="/products?new=true">New Arrivals</Link></li>
                    <li><Link to="/products?featured=true">Bestsellers</Link></li>
                    <li><Link to="/products">All Products</Link></li>
                    <li><Link to="/products?sale=true">Sale</Link></li>
                    <li><Link to="/products?featured=true">Featured</Link></li>
                  </ul>
                </div>
              </div>

              <div className="col-lg-2 col-md-6 col-sm-6">
                <div className="footer-widget">
                  <h4>Support</h4>
                  <ul className="footer-links">
                    <li><Link to="/contact">Help Center</Link></li>
                    <li><Link to="/account/orders">Order Status</Link></li>
                    <li><Link to="/shipping">Shipping Info</Link></li>
                    <li><Link to="/returns">Returns &amp; Exchanges</Link></li>
                    <li><Link to="/faq">FAQs</Link></li>
                    <li><Link to="/contact">Contact Us</Link></li>
                  </ul>
                </div>
              </div>

              <div className="col-lg-4 col-md-6">
                <div className="footer-widget">
                  <h4>Contact Information</h4>
                  <div className="footer-contact">
                    <div className="contact-item">
                      <i className="bi bi-telephone"></i>
                      <span>+91-9711317009</span>
                    </div>
                    <div className="contact-item">
                      <i className="bi bi-envelope"></i>
                      <span>support@pavitraenterprises.com</span>
                    </div>
                    <div className="contact-item">
                      <i className="bi bi-clock"></i>
                      <span>Monday-Friday: 9am-6pm<br/>Saturday: 10am-4pm<br/>Sunday: Closed</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="footer-bottom">
          <div className="container">
            <div className="row gy-3 align-items-center">
              <div className="col-lg-6 col-md-12">
                <div className="copyright">
                  <p>© <span>Copyright</span> <strong className="sitename">Pavitra Enterprises</strong>. All Rights Reserved.</p>
                </div>
              </div>

              <div className="col-lg-6 col-md-12">
                <div className="d-flex flex-wrap justify-content-lg-end justify-content-center align-items-center gap-4">
                  <div className="payment-methods">
                    <div className="payment-icons">
                      <i className="bi bi-credit-card" aria-label="Credit Card"></i>
                      <i className="bi bi-cash" aria-label="Cash on Delivery"></i>
                      <i className="bi bi-bank" aria-label="Net Banking"></i>
                    </div>
                  </div>

                  <div className="legal-links">
                    <Link to="/terms">Terms</Link>
                    <Link to="/privacy">Privacy</Link>
                    <Link to="/returns">Returns</Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </footer>

      {/* Scroll Top */}
      <a href="#" id="scroll-top" className="scroll-top d-flex align-items-center justify-content-center"><i className="bi bi-arrow-up-short"></i></a>

      {/* Preloader */}
      <div id="preloader"></div>
    </div>
  );
};

export default BaseLayout;
