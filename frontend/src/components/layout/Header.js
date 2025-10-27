import React from 'react';
import { useAuth } from '../../context/AuthContext';
import UserMenu from '../common/UserMenu';

const Header = () => {
  const { isAuthenticated, user } = useAuth();

  return (
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
            <a href="/" className="logo d-flex align-items-center text-decoration-none">
              <h1 className="sitename">Pavitra Enterprises</h1>
            </a>

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
              {/* Mobile Search Toggle */}
              <button className="header-action-btn mobile-search-toggle d-xl-none" type="button" data-bs-toggle="collapse" data-bs-target="#mobileSearch" aria-expanded="false" aria-controls="mobileSearch">
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
              <a href="/account?tab=wishlist" className="header-action-btn d-none d-md-block position-relative">
                <i className="bi bi-heart"></i>
                <span className="badge" id="wishlist-count">0</span>
              </a>

              {/* Cart */}
              <a href="/cart" className="header-action-btn position-relative">
                <i className="bi bi-cart3"></i>
                <span className="badge" id="cart-count">0</span>
              </a>

              {/* Mobile Navigation Toggle */}
              <i className="mobile-nav-toggle d-xl-none bi bi-list me-0"></i>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="header-nav">
        <div className="container-fluid container-xl position-relative">
          <nav id="navmenu" className="navmenu">
            <ul>
              <li><a href="/" className="active">Home</a></li>
              <li><a href="/about">About</a></li>

              {/* Products Mega Menu */}
              <li className="products-megamenu-1">
                <a href="#"><span>Shop</span> <i className="bi bi-chevron-down toggle-dropdown"></i></a>

                {/* Mobile View */}
                <ul className="mobile-megamenu">
                  <li><a href="/products">All Products</a></li>
                  <li><a href="/products?featured=true">Featured Products</a></li>
                  <li><a href="/products?new_arrivals=true">New Arrivals</a></li>
                  <li><a href="/products?on_sale=true">On Sale</a></li>
                </ul>

                {/* Desktop View */}
                <div className="desktop-megamenu">
                  <div className="megamenu-tabs">
                    <ul className="nav nav-tabs" id="productMegaMenuTabs" role="tablist">
                      <li className="nav-item" role="presentation">
                        <button className="nav-link active" id="featured-tab" data-bs-toggle="tab" data-bs-target="#featured-content" type="button" aria-selected="true" role="tab">Featured</button>
                      </li>
                      <li className="nav-item" role="presentation">
                        <button className="nav-link" id="new-tab" data-bs-toggle="tab" data-bs-target="#new-content" type="button" aria-selected="false" tabindex="-1" role="tab">New Arrivals</button>
                      </li>
                      <li className="nav-item" role="presentation">
                        <button className="nav-link" id="categories-tab" data-bs-toggle="tab" data-bs-target="#categories-content" type="button" aria-selected="false" tabindex="-1" role="tab">Categories</button>
                      </li>
                    </ul>
                  </div>

                  {/* Tabs Content */}
                  <div className="megamenu-content tab-content">
                    {/* Featured Tab */}
                    <div className="tab-pane fade show active" id="featured-content" role="tabpanel" aria-labelledby="featured-tab">
                      <div className="product-grid">
                        <div className="text-center py-4 w-100">
                          <p className="text-muted">Featured products will appear here</p>
                          <a href="/products" className="btn btn-sm btn-outline-primary">Browse All Products</a>
                        </div>
                      </div>
                    </div>

                    {/* New Arrivals Tab */}
                    <div className="tab-pane fade" id="new-content" role="tabpanel" aria-labelledby="new-tab">
                      <div className="product-grid">
                        <div className="text-center py-4 w-100">
                          <p className="text-muted">New arrivals will appear here</p>
                          <a href="/products" className="btn btn-sm btn-outline-primary">Browse All Products</a>
                        </div>
                      </div>
                    </div>

                    {/* Categories Tab */}
                    <div className="tab-pane fade" id="categories-content" role="tabpanel" aria-labelledby="categories-tab">
                      <div className="category-grid">
                        <div className="text-center py-4 w-100">
                          <p className="text-muted">Categories will appear here</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </li>

              <li><a href="/contact">Contact</a></li>
            </ul>
          </nav>
        </div>
      </div>

      {/* Mobile Search Form */}
      <div className="collapse" id="mobileSearch">
        <div className="container">
          <form className="search-form" action="/search" method="GET">
            <div className="input-group">
              <input type="text" className="form-control" name="q" placeholder="Search for products" />
              <button className="btn" type="submit">
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
