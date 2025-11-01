import React from 'react';
import { Link } from 'react-router-dom';
import { useSettings } from '../../../contexts/SettingsContext';
import { useAuth } from '../../../contexts/AuthContext';
import { useCartContext } from '../../../contexts/CartContext'; // CHANGE THIS

const MainHeader = () => {
  const { frontendSettings } = useSettings();
  const { isAuthenticated, user, logout } = useAuth();
  const { cart, loading: cartLoading } = useCartContext(); // CHANGE THIS

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  // Use the total_items from cart context
  const totalCartItems = cart?.total_items || 0;

  return (
    <div className="main-header">
      <div className="container-fluid container-xl">
        <div className="d-flex py-3 align-items-center justify-content-between">
          <Link to="/" className="logo d-flex align-items-center">
            <h1 className="sitename">{frontendSettings.site_name || 'Pavitra Trading'}</h1>
          </Link>

          <form className="search-form desktop-search-form">
            <div className="input-group">
              <input type="text" className="form-control" placeholder="Search for products" />
              <button className="btn" type="submit">
                <i className="bi bi-search"></i>
              </button>
            </div>
          </form>

          <div className="header-actions d-flex align-items-center justify-content-end">
            <button className="header-action-btn mobile-search-toggle d-xl-none" type="button">
              <i className="bi bi-search"></i>
            </button>

            <div className="dropdown account-dropdown">
              <button className="header-action-btn" data-bs-toggle="dropdown">
                <i className="bi bi-person"></i>
              </button>
              <div className="dropdown-menu">
                {isAuthenticated ? (
                  <>
                    <div className="dropdown-header">
                      <h6>Welcome, {user?.first_name || 'User'}!</h6>
                      <p className="mb-0 text-muted">{user?.email}</p>
                    </div>
                    <div className="dropdown-body">
                      <Link className="dropdown-item" to="/account">My Profile</Link>
                      <Link className="dropdown-item" to="/orders">My Orders</Link>
                      <Link className="dropdown-item" to="/wishlist">My Wishlist</Link>
                    </div>
                    <div className="dropdown-footer">
                      <button className="btn btn-outline-danger w-100" onClick={handleLogout}>
                        Logout
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="dropdown-header">
                      <h6>Welcome</h6>
                      <p className="mb-0">Access account & manage orders</p>
                    </div>
                    <div className="dropdown-body">
                      <Link className="dropdown-item" to="/auth?form=login">Sign In</Link>
                      <Link className="dropdown-item" to="/auth?form=register">Create Account</Link>
                    </div>
                  </>
                )}
              </div>
            </div>

            <Link to="/wishlist" className="header-action-btn d-none d-md-block">
              <i className="bi bi-heart"></i>
            </Link>

            <Link to="/cart" className="header-action-btn position-relative">
              <i className="bi bi-cart3"></i>
              {!cartLoading && totalCartItems > 0 ? (
                <span className="badge bg-primary position-absolute top-0 start-100 translate-middle">
                  {totalCartItems > 99 ? '99+' : totalCartItems}
                </span>
              ) : (
                <span className="badge bg-secondary position-absolute top-0 start-100 translate-middle" style={{opacity: 0.5}}>
                  0
                </span>
              )}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MainHeader;