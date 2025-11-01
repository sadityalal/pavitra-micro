// frontend/src/components/layout/Header/MainHeader.js
import React from 'react';
import { useSettings } from '../../../contexts/SettingsContext';

const MainHeader = () => {
  const { frontendSettings } = useSettings();

  return (
    <div className="main-header">
      <div className="container-fluid container-xl">
        <div className="d-flex py-3 align-items-center justify-content-between">
          {/* Logo */}
          <a href="/" className="logo d-flex align-items-center">
            <h1 className="sitename">{frontendSettings.site_name || 'Pavitra Trading'}</h1>
          </a>
          
          {/* Search Form */}
          <form className="search-form desktop-search-form">
            <div className="input-group">
              <input type="text" className="form-control" placeholder="Search for products" />
              <button className="btn" type="submit">
                <i className="bi bi-search"></i>
              </button>
            </div>
          </form>
          
          {/* Header Actions */}
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
              <div className="dropdown-menu">
                <div className="dropdown-header">
                  <h6>Welcome to <span className="sitename">{frontendSettings.site_name || 'Pavitra Trading'}</span></h6>
                  <p className="mb-0">Access account &amp; manage orders</p>
                </div>
                <div className="dropdown-body">
                  <a className="dropdown-item d-flex align-items-center" href="/account">
                    <i className="bi bi-person-circle me-2"></i>
                    <span>My Profile</span>
                  </a>
                  <a className="dropdown-item d-flex align-items-center" href="/account">
                    <i className="bi bi-bag-check me-2"></i>
                    <span>My Orders</span>
                  </a>
                  <a className="dropdown-item d-flex align-items-center" href="/account">
                    <i className="bi bi-heart me-2"></i>
                    <span>My Wishlist</span>
                  </a>
                  <a className="dropdown-item d-flex align-items-center" href="/account">
                    <i className="bi bi-gear me-2"></i>
                    <span>Settings</span>
                  </a>
                </div>
                <div className="dropdown-footer">
                  <a href="/register" className="btn btn-primary w-100 mb-2">Sign In</a>
                  <a href="/login" className="btn btn-outline-primary w-100">Register</a>
                </div>
              </div>
            </div>
            
            {/* Wishlist */}
            <a href="/account" className="header-action-btn d-none d-md-block">
              <i className="bi bi-heart"></i>
              <span className="badge">0</span>
            </a>
            
            {/* Cart */}
            <a href="/cart" className="header-action-btn">
              <i className="bi bi-cart3"></i>
              <span className="badge">3</span>
            </a>
            
            {/* Mobile Nav Toggle */}
            <i className="mobile-nav-toggle d-xl-none bi bi-list me-0"></i>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MainHeader;