// frontend/src/components/layout/Header.js
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useCart } from '../../context/CartContext';
import UserMenu from '../common/UserMenu';
import { Link } from 'react-router-dom';

const Header = () => {
  const { isAuthenticated, user, siteSettings } = useAuth();
  const { totalItems } = useCart();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  useEffect(() => {
    // Initialize AOS and other animations
    if (typeof window !== 'undefined') {
      setTimeout(() => {
        if (window.AOS) {
          window.AOS.init({
            duration: 1000,
            easing: 'ease-in-out',
            once: true,
            mirror: false
          });
        }
      }, 100);
    }
  }, []);

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const toggleSearch = () => {
    setIsSearchOpen(!isSearchOpen);
  };

  return (
    <header id="header" className="header sticky-top">
      {/* Top Bar */}
      <div className="top-bar py-2 d-none d-lg-block">
        <div className="container-fluid container-xl">
          <div className="row align-items-center">
            <div className="col-lg-4">
              <div className="top-bar-item">
                <i className="bi bi-telephone-fill me-2"></i>
                <span>Need help? Call us: </span>
                <a href="tel:+919711317009">+91-9711317009</a>
              </div>
            </div>
            <div className="col-lg-4 text-center">
              <div className="announcement-slider">
                <div className="swiper-wrapper">
                  <div className="swiper-slide">🚚 Free shipping on orders over {siteSettings.currency_symbol || '₹'}{siteSettings.free_shipping_threshold || 999}</div>
                  <div className="swiper-slide">💰 {siteSettings.return_period_days || 10}-day money back guarantee</div>
                  <div className="swiper-slide">🎁 20% off on your first order</div>
                </div>
              </div>
            </div>
            <div className="col-lg-4">
              <div className="d-flex justify-content-end">
                <div className="top-bar-item dropdown me-3">
                  <a href="#" className="dropdown-toggle" data-bs-toggle="dropdown">
                    <i className="bi bi-translate me-2"></i>EN
                  </a>
                  <ul className="dropdown-menu">
                    <li><a className="dropdown-item" href="#"><i className="bi bi-check2 me-2"></i>English</a></li>
                    <li><a className="dropdown-item" href="#">Hindi</a></li>
                  </ul>
                </div>
                <div className="top-bar-item dropdown">
                  <a href="#" className="dropdown-toggle" data-bs-toggle="dropdown">
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
      <div className="main-header">
        <div className="container-fluid container-xl">
          <div className="d-flex py-3 align-items-center justify-content-between">
            {/* Logo */}
            <Link to="/" className="logo d-flex align-items-center text-decoration-none">
              <h1 className="sitename mb-0">Pavitra Enterprises</h1>
            </Link>

            {/* Search Form */}
            <form className="search-form desktop-search-form d-none d-xl-flex" action="/search" method="GET">
              <div className="input-group">
                <input type="text" className="form-control" name="q" placeholder="Search for products" />
                <button className="btn btn-primary" type="submit">
                  <i className="bi bi-search"></i>
                </button>
              </div>
            </form>

            {/* Header Actions */}
            <div className="header-actions d-flex align-items-center">
              {/* Mobile Search Toggle */}
              <button
                className="header-action-btn mobile-search-toggle d-xl-none"
                type="button"
                onClick={toggleSearch}
              >
                <i className="bi bi-search"></i>
              </button>

              {/* Account Dropdown */}
              <div className="dropdown account-dropdown">
                <button className="header-action-btn" data-bs-toggle="dropdown">
                  <i className="bi bi-person"></i>
                </button>
                <div className="dropdown-menu dropdown-menu-end">
                  <UserMenu />
                </div>
              </div>

              {/* Wishlist */}
              <Link to="/account?tab=wishlist" className="header-action-btn d-none d-md-flex position-relative">
                <i className="bi bi-heart"></i>
                <span className="badge bg-primary">0</span>
              </Link>

              {/* Cart */}
              <Link to="/cart" className="header-action-btn position-relative">
                <i className="bi bi-cart3"></i>
                <span className="badge bg-primary" id="cart-count">{totalItems}</span>
              </Link>

              {/* Mobile Navigation Toggle */}
              <button
                className="mobile-nav-toggle d-xl-none btn btn-link text-decoration-none p-0 ms-2"
                onClick={toggleMobileMenu}
              >
                <i className="bi bi-list" style={{fontSize: '1.5rem'}}></i>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className={`header-nav d-none d-xl-block ${isMobileMenuOpen ? 'd-block' : ''}`}>
        <div className="container-fluid container-xl position-relative">
          <nav id="navmenu" className="navmenu">
            <ul className="d-flex flex-column flex-xl-row mb-0">
              <li className="nav-item">
                <Link to="/" className="nav-link active">Home</Link>
              </li>
              <li className="nav-item">
                <Link to="/about" className="nav-link">About</Link>
              </li>

              {/* Products Mega Menu */}
              <li className="nav-item dropdown products-megamenu-1">
                <a href="#" className="nav-link dropdown-toggle" data-bs-toggle="dropdown">
                  <span>Shop</span> <i className="bi bi-chevron-down ms-1"></i>
                </a>
                <div className="dropdown-menu dropdown-menu-start p-3" style={{minWidth: '300px'}}>
                  <Link className="dropdown-item" to="/products">All Products</Link>
                  <Link className="dropdown-item" to="/products?featured=true">Featured Products</Link>
                  <Link className="dropdown-item" to="/products?new_arrivals=true">New Arrivals</Link>
                  <Link className="dropdown-item" to="/products?on_sale=true">On Sale</Link>
                  <div className="dropdown-divider"></div>
                  <Link className="dropdown-item" to="/categories">Browse Categories</Link>
                </div>
              </li>

              <li className="nav-item">
                <Link to="/contact" className="nav-link">Contact</Link>
              </li>
            </ul>
          </nav>
        </div>
      </div>

      {/* Mobile Search Form */}
      <div className={`collapse ${isSearchOpen ? 'show' : ''}`} id="mobileSearch">
        <div className="container py-2">
          <form className="search-form" action="/search" method="GET">
            <div className="input-group">
              <input type="text" className="form-control" name="q" placeholder="Search for products" />
              <button className="btn btn-primary" type="submit">
                <i className="bi bi-search"></i>
              </button>
            </div>
          </form>
        </div>
      </div>
    </header>
  );
};

export default Header;