import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { useCart } from '../../context/CartContext';
import UserMenu from '../common/UserMenu';

const Header = () => {
  const { isAuthenticated, user } = useAuth();
  const { totalItems } = useCart();

  return (
    <header id="header" className="header sticky-top">
      {/* ... rest of the header code remains the same ... */}
      
      {/* Cart with dynamic count */}
      <a href="/cart" className="header-action-btn position-relative">
        <i className="bi bi-cart3"></i>
        <span className="badge" id="cart-count">{totalItems}</span>
      </a>

      {/* ... rest of the header code remains the same ... */}
    </header>
  );
};

export default Header;
