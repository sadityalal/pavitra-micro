import React from 'react';
import { useSettings } from '../../../contexts/SettingsContext';
import { useAuth } from '../../../contexts/AuthContext';
import { Link } from 'react-router-dom';

const MainHeader = () => {
  const { frontendSettings } = useSettings();
  const { isAuthenticated, user, logout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

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

            {/* User Account Dropdown */}
            <div className="dropdown account-dropdown">
              <button className="header-action-btn" data-bs-toggle="dropdown">
                <i className="bi bi-person"></i>
              </button>
              <div className="dropdown-menu">
                {isAuthenticated ? (
                  /* Logged In State - Show User Menu */
                  <>
                    <div className="dropdown-header">
                      <h6>Welcome, {user?.first_name || 'User'}!</h6>
                      <p className="mb-0 text-muted">{user?.email}</p>
                    </div>
                    <div className="dropdown-body">
                      <a className="dropdown-item d-flex align-items-center" href="/account">
                        <i className="bi bi-person-circle me-2"></i>
                        <span>My Profile</span>
                      </a>
                      <a className="dropdown-item d-flex align-items-center" href="/orders">
                        <i className="bi bi-bag-check me-2"></i>
                        <span>My Orders</span>
                      </a>
                      <a className="dropdown-item d-flex align-items-center" href="/wishlist">
                        <i className="bi bi-heart me-2"></i>
                        <span>My Wishlist</span>
                      </a>
                      <a className="dropdown-item d-flex align-items-center" href="/settings">
                        <i className="bi bi-gear me-2"></i>
                        <span>Settings</span>
                      </a>
                    </div>
                    <div className="dropdown-footer">
                      <button className="btn btn-outline-danger w-100" onClick={handleLogout}>
                        <i className="bi bi-box-arrow-right me-2"></i>
                        Logout
                      </button>
                    </div>
                  </>
                ) : (
                  /* Logged Out State - Show Login/Register */
                  <>
                    <div className="dropdown-header">
                      <h6>Welcome to <span className="sitename">{frontendSettings.site_name || 'Pavitra Trading'}</span></h6>
                      <p className="mb-0">Access account &amp; manage orders</p>
                    </div>
                    <div className="dropdown-body">
                      <Link className="dropdown-item d-flex align-items-center" to="/auth?form=login">
                        <i className="bi bi-box-arrow-in-right me-2"></i>
                        <span>Sign In</span>
                      </Link>
                      <Link className="dropdown-item d-flex align-items-center" to="/auth?form=register">
                        <i className="bi bi-person-plus me-2"></i>
                        <span>Create Account</span>
                      </Link>
                    </div>
                    <div className="dropdown-footer">
                      <Link to="/auth?form=login" className="btn btn-dark w-100 mb-2">Sign In</Link>
                      <Link to="/auth?form=register" className="btn btn-outline-dark w-100">Create Account</Link>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Wishlist */}
            <a href="/wishlist" className="header-action-btn d-none d-md-block">
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