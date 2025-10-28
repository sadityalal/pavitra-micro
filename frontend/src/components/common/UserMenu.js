import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const UserMenu = () => {
  const { user, logout, isAuthenticated } = useAuth();

  if (isAuthenticated) {
    return (
      <>
        <div className="dropdown-header">
          <h6>Welcome, <span className="text-primary">{user?.name || user?.email?.split('@')[0]}</span></h6>
          <p className="mb-0">Access account & manage orders</p>
        </div>
        <div className="dropdown-body">
          <Link className="dropdown-item d-flex align-items-center" to="/account?tab=orders">
            <i className="bi bi-person-circle me-2"></i>
            <span>My Account</span>
          </Link>
          <Link className="dropdown-item d-flex align-items-center" to="/account?tab=orders">
            <i className="bi bi-bag-check me-2"></i>
            <span>My Orders</span>
          </Link>
          <Link className="dropdown-item d-flex align-items-center" to="/account?tab=wishlist">
            <i className="bi bi-heart me-2"></i>
            <span>My Wishlist</span>
          </Link>
          <Link className="dropdown-item d-flex align-items-center" to="/account?tab=addresses">
            <i className="bi bi-geo-alt me-2"></i>
            <span>My Addresses</span>
          </Link>
        </div>
        <div className="dropdown-footer">
          <button onClick={logout} className="btn btn-outline-primary w-100 btn-sm">
            Logout
          </button>
        </div>
      </>
    );
  }

  return (
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
  );
};

export default UserMenu;
