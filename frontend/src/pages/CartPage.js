import React from 'react';
import { useCart } from '../hooks/useCart';
import { useSettings } from '../contexts/SettingsContext';
import { Link } from 'react-router-dom';

const CartPage = () => {
  const { cart, loading, updateCartItem, removeFromCart, clearCart } = useCart();
  const { frontendSettings } = useSettings();

  const handleQuantityChange = async (cartItemId, newQuantity) => {
    if (newQuantity < 1) return;
    try {
      await updateCartItem(cartItemId, newQuantity);
    } catch (error) {
      console.error('Failed to update quantity:', error);
      alert(error.message || 'Failed to update quantity');
    }
  };

  const handleRemoveItem = async (cartItemId) => {
    try {
      await removeFromCart(cartItemId);
    } catch (error) {
      console.error('Failed to remove item:', error);
      alert(error.message || 'Failed to remove item from cart');
    }
  };

  const handleClearCart = async () => {
    if (window.confirm('Are you sure you want to clear your cart?')) {
      try {
        await clearCart();
      } catch (error) {
        console.error('Failed to clear cart:', error);
        alert(error.message || 'Failed to clear cart');
      }
    }
  };

  if (loading) {
    return (
      <div className="container py-5">
        <div className="text-center">
          <div className="spinner-border" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container py-5">
      <div className="row">
        <div className="col-12">
          <h1 className="mb-4">Shopping Cart</h1>
        </div>
      </div>
      {cart.items.length === 0 ? (
        <div className="text-center py-5">
          <i className="bi bi-cart-x display-1 text-muted"></i>
          <h3 className="mt-3">Your cart is empty</h3>
          <p className="text-muted">Start shopping to add items to your cart</p>
          <Link to="/products" className="btn btn-primary">
            Continue Shopping
          </Link>
        </div>
      ) : (
        <div className="row">
          <div className="col-lg-8">
            <div className="card">
              <div className="card-header d-flex justify-content-between align-items-center">
                <h5 className="mb-0">
                  Cart Items ({cart.total_items})
                </h5>
                <button
                  className="btn btn-outline-danger btn-sm"
                  onClick={handleClearCart}
                >
                  Clear Cart
                </button>
              </div>
              <div className="card-body">
                {cart.items.map((item) => (
                  <div key={item.id} className="cart-item border-bottom pb-3 mb-3">
                    <div className="row align-items-center">
                      <div className="col-md-2">
                        <img
                          src={item.product_image || '/assets/img/product/placeholder.jpg'}
                          alt={item.product_name}
                          className="img-fluid rounded"
                          style={{ maxHeight: '80px', objectFit: 'cover' }}
                        />
                      </div>
                      <div className="col-md-4">
                        <h6 className="mb-1">{item.product_name}</h6>
                        <p className="text-muted small mb-0">{item.variation_name}</p>
                      </div>
                      <div className="col-md-2">
                        <span className="fw-bold">
                          {frontendSettings.currency_symbol}{item.product_price || item.unit_price}
                        </span>
                      </div>
                      <div className="col-md-2">
                        <div className="input-group input-group-sm">
                          <button
                            className="btn btn-outline-secondary"
                            type="button"
                            onClick={() => handleQuantityChange(item.id, item.quantity - 1)}
                            disabled={item.quantity <= 1}
                          >
                            -
                          </button>
                          <input
                            type="text"
                            className="form-control text-center"
                            value={item.quantity}
                            readOnly
                            style={{ maxWidth: '60px' }}
                          />
                          <button
                            className="btn btn-outline-secondary"
                            type="button"
                            onClick={() => handleQuantityChange(item.id, item.quantity + 1)}
                          >
                            +
                          </button>
                        </div>
                      </div>
                      <div className="col-md-2">
                        <span className="fw-bold">
                          {frontendSettings.currency_symbol}{item.total_price || (item.product_price * item.quantity)}
                        </span>
                        <button
                          className="btn btn-outline-danger btn-sm ms-2"
                          onClick={() => handleRemoveItem(item.id)}
                        >
                          <i className="bi bi-trash"></i>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="col-lg-4">
            <div className="card">
              <div className="card-header">
                <h5 className="mb-0">Order Summary</h5>
              </div>
              <div className="card-body">
                <div className="d-flex justify-content-between mb-2">
                  <span>Subtotal:</span>
                  <span>{frontendSettings.currency_symbol}{cart.subtotal || cart.total}</span>
                </div>
                <div className="d-flex justify-content-between mb-2">
                  <span>Shipping:</span>
                  <span className="text-success">
                    {cart.subtotal >= frontendSettings.free_shipping_min_amount
                      ? 'FREE'
                      : `Calculated at checkout`
                    }
                  </span>
                </div>
                <hr />
                <div className="d-flex justify-content-between mb-3">
                  <strong>Total:</strong>
                  <strong>{frontendSettings.currency_symbol}{cart.total}</strong>
                </div>
                <Link to="/checkout" className="btn btn-primary w-100 mb-2">
                  Proceed to Checkout
                </Link>
                <Link to="/products" className="btn btn-outline-secondary w-100">
                  Continue Shopping
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CartPage;