import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useSiteSettings } from '../contexts/SiteSettingsContext'
import { useCart } from '../contexts/CartContext'
import { useAuth } from '../contexts/AuthContext'

const Header = () => {
  const { settings } = useSiteSettings()
  const { cartCount, wishlistCount } = useCart()
  const { user, logout } = useAuth()
  const [mobileSearchOpen, setMobileSearchOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const navigate = useNavigate()

  const handleSearch = (e) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/products?search=${encodeURIComponent(searchQuery)}`)
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <header className="header sticky-top">
      {/* Top Bar */}
      <div className="top-bar py-2 bg-light border-bottom">
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
              <div className="announcement-slider">
                <div className="swiper-wrapper">
                  <div className="swiper-slide">
                    🚚 Free shipping on orders over {settings.currency_symbol}{settings.free_shipping_min_amount || '999'}
                  </div>
                  <div className="swiper-slide">
                    💰 30-day money back guarantee
                  </div>
                  <div className="swiper-slide">
                    🎁 20% off on your first order
                  </div>
                </div>
              </div>
            </div>

            <div className="col-lg-4 d-none d-lg-block">
              <div className="d-flex justify-content-end">
                <div className="top-bar-item dropdown me-3">
                  <a href="#" className="dropdown-toggle text-decoration-none text-dark" data-bs-toggle="dropdown">
                    <i className="bi bi-translate me-2"></i>EN
                  </a>
                  <ul className="dropdown-menu">
                    <li><a className="dropdown-item" href="#"><i className="bi bi-check2 me-2"></i>English</a></li>
                    <li><a className="dropdown-item" href="#">Hindi</a></li>
                  </ul>
                </div>
                <div className="top-bar-item dropdown">
                  <a href="#" className="dropdown-toggle text-decoration-none text-dark" data-bs-toggle="dropdown">
                    <i className="bi bi-currency-rupee me-2"></i>INR
                  </a>
                  <ul className="dropdown-menu">
                    <li><a className="dropdown-item" href="#"><i className="bi bi-check2 me-2"></i>INR</a></li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Header */}
      <div className="main-header bg-white border-bottom">
        <div className="container-fluid container-xl">
          <div className="d-flex py-3 align-items-center justify-content-between">
            {/* Logo */}
            <Link to="/" className="logo d-flex align-items-center text-decoration-none">
              <h1 className="sitename h3 mb-0 text-primary">{settings.site_name || 'Pavitra Trading'}</h1>
            </Link>

            {/* Search Form */}
            <form className="search-form desktop-search-form d-none d-xl-flex mx-4 flex-grow-1" onSubmit={handleSearch}>
              <div className="input-group">
                <input 
                  type="text" 
                  className="form-control" 
                  placeholder="Search for products" 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <button className="btn btn-primary" type="submit">
                  <i className="bi bi-search"></i>
                </button>
              </div>
            </form>

            {/* Actions */}
            <div className="header-actions d-flex align-items-center justify-content-end">
              {/* Mobile Search Toggle */}
              <button 
                className="header-action-btn mobile-search-toggle d-xl-none btn btn-link text-dark" 
                type="button" 
                onClick={() => setMobileSearchOpen(!mobileSearchOpen)}
              >
                <i className="bi bi-search"></i>
              </button>

              {/* Account Dropdown */}
              <div className="dropdown account-dropdown ms-3">
                <button className="header-action-btn btn btn-link text-dark" data-bs-toggle="dropdown">
                  <i className="bi bi-person"></i>
                </button>
                <div className="dropdown-menu dropdown-menu-end">
                  {user ? (
                    <>
                      <div className="dropdown-header">
                        <h6>Welcome, <span className="text-primary">{user.first_name || user.email.split('@')[0]}</span></h6>
                        <p className="mb-0">Access account & manage orders</p>
                      </div>
                      <div className="dropdown-body">
                        <Link className="dropdown-item d-flex align-items-center" to="/account">
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
                        <button onClick={handleLogout} className="btn btn-outline-primary w-100 btn-sm">Logout</button>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="dropdown-header">
                        <h6>Welcome to <span className="text-primary">{settings.site_name || 'Pavitra Trading'}</span></h6>
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
              <Link to="/account/wishlist" className="header-action-btn d-none d-md-block position-relative ms-3 text-dark text-decoration-none">
                <i className="bi bi-heart"></i>
                <span className="badge bg-primary position-absolute top-0 start-100 translate-middle">
                  {wishlistCount}
                </span>
              </Link>

              {/* Cart */}
              <Link to="/cart" className="header-action-btn position-relative ms-3 text-dark text-decoration-none">
                <i className="bi bi-cart3"></i>
                <span className="badge bg-primary position-absolute top-0 start-100 translate-middle">
                  {cartCount}
                </span>
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Search Form */}
      {mobileSearchOpen && (
        <div className="container-fluid bg-light py-2 border-bottom">
          <form className="search-form" onSubmit={handleSearch}>
            <div className="input-group">
              <input 
                type="text" 
                className="form-control" 
                placeholder="Search for products" 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <button className="btn btn-primary" type="submit">
                <i className="bi bi-search"></i>
              </button>
            </div>
          </form>
        </div>
      )}
    </header>
  )
}

export default Header
