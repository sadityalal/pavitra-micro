import React, { useState } from 'react';
import { useCartContext } from '../contexts/CartContext';
import { useSettings } from '../contexts/SettingsContext';
import { useToast } from '../contexts/ToastContext';
import { Link } from 'react-router-dom';

const CartPage = () => {
  const { cart, loading, updateCartItem, removeFromCart, clearCart } = useCartContext();
  const { frontendSettings } = useSettings();
  const { success, error, warning, info } = useToast();
  const [updatingItems, setUpdatingItems] = useState({});

  const handleQuantityChange = async (cartItemId, newQuantity) => {
    if (newQuantity < 1) {
      // Show beautiful confirmation for removal
      if (window.confirm('Are you sure you want to remove this item from your cart?')) {
        await handleRemoveItem(cartItemId);
      }
      return;
    }

    try {
      setUpdatingItems(prev => ({ ...prev, [cartItemId]: true }));
      await updateCartItem(cartItemId, newQuantity);
      info('Cart updated successfully');
    } catch (err) {
      console.error('Failed to update quantity:', err);
      error(err.message || 'Failed to update quantity');
    } finally {
      setUpdatingItems(prev => ({ ...prev, [cartItemId]: false }));
    }
  };

  const handleIncrement = async (cartItemId, currentQuantity, maxQuantity = 20) => {
    const newQuantity = currentQuantity + 1;
    if (newQuantity > maxQuantity) {
      warning(`Maximum quantity limit reached (${maxQuantity})`);
      return;
    }
    await handleQuantityChange(cartItemId, newQuantity);
  };

  const handleDecrement = async (cartItemId, currentQuantity) => {
    const newQuantity = currentQuantity - 1;
    if (newQuantity === 0) {
      // Show beautiful confirmation dialog
      showRemoveConfirmation(cartItemId);
    } else {
      await handleQuantityChange(cartItemId, newQuantity);
    }
  };

  const showRemoveConfirmation = (cartItemId) => {
    // Create a beautiful modal-like confirmation
    const confirmationDiv = document.createElement('div');
    confirmationDiv.className = 'remove-confirmation-modal';
    confirmationDiv.innerHTML = `
      <div class="confirmation-overlay">
        <div class="confirmation-dialog">
          <div class="confirmation-header">
            <h5>Remove Item</h5>
            <button type="button" class="btn-close confirmation-close"></button>
          </div>
          <div class="confirmation-body">
            <p>Are you sure you want to remove this item from your cart?</p>
          </div>
          <div class="confirmation-footer">
            <button class="btn btn-secondary confirmation-cancel">Cancel</button>
            <button class="btn btn-danger confirmation-remove">Remove</button>
          </div>
        </div>
      </div>
    `;

    // Add styles
    const styles = `
      .remove-confirmation-modal .confirmation-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
      }
      .remove-confirmation-modal .confirmation-dialog {
        background: white;
        border-radius: 8px;
        padding: 0;
        max-width: 400px;
        width: 90%;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
      }
      .remove-confirmation-modal .confirmation-header {
        padding: 1rem 1.5rem;
        border-bottom: 1px solid #dee2e6;
        display: flex;
        justify-content: between;
        align-items: center;
      }
      .remove-confirmation-modal .confirmation-header h5 {
        margin: 0;
        flex: 1;
      }
      .remove-confirmation-modal .confirmation-body {
        padding: 1.5rem;
      }
      .remove-confirmation-modal .confirmation-footer {
        padding: 1rem 1.5rem;
        border-top: 1px solid #dee2e6;
        display: flex;
        gap: 0.5rem;
        justify-content: flex-end;
      }
      .remove-confirmation-modal .confirmation-close {
        border: none;
        background: none;
        font-size: 1.2rem;
        cursor: pointer;
      }
    `;

    const styleSheet = document.createElement('style');
    styleSheet.textContent = styles;
    document.head.appendChild(styleSheet);
    document.body.appendChild(confirmationDiv);

    // Add event listeners
    const closeBtn = confirmationDiv.querySelector('.confirmation-close');
    const cancelBtn = confirmationDiv.querySelector('.confirmation-cancel');
    const removeBtn = confirmationDiv.querySelector('.confirmation-remove');

    const cleanup = () => {
      document.body.removeChild(confirmationDiv);
      document.head.removeChild(styleSheet);
    };

    closeBtn.onclick = cleanup;
    cancelBtn.onclick = cleanup;
    removeBtn.onclick = async () => {
      await handleRemoveItem(cartItemId);
      cleanup();
    };
  };

  const handleRemoveItem = async (cartItemId) => {
    try {
      await removeFromCart(cartItemId);
      success('Item removed from cart');
    } catch (err) {
      console.error('Failed to remove item:', err);
      error(err.message || 'Failed to remove item from cart');
    }
  };

  const handleClearCart = async () => {
    if (window.confirm('Are you sure you want to clear your entire cart?')) {
      try {
        await clearCart();
        success('Cart cleared successfully');
      } catch (err) {
        console.error('Failed to clear cart:', err);
        error(err.message || 'Failed to clear cart');
      }
    }
  };

  if (loading && cart.items.length === 0) {
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
                  disabled={loading}
                >
                  {loading ? 'Clearing...' : 'Clear Cart'}
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
                          onError={(e) => {
                            e.target.src = '/assets/img/product/placeholder.jpg';
                          }}
                        />
                      </div>
                      <div className="col-md-4">
                        <h6 className="mb-1">{item.product_name}</h6>
                        <p className="text-muted small mb-0">
                          {item.variation_name || 'Standard'}
                        </p>
                        {item.stock_status === 'out_of_stock' && (
                          <span className="badge bg-danger mt-1">Out of Stock</span>
                        )}
                        {item.stock_quantity > 0 && item.stock_quantity <= 5 && (
                          <span className="badge bg-warning mt-1">Only {item.stock_quantity} left</span>
                        )}
                      </div>
                      <div className="col-md-2">
                        <span className="fw-bold">
                          {frontendSettings.currency_symbol}{item.product_price || item.unit_price}
                        </span>
                      </div>
                      <div className="col-md-2">
                        <div className="input-group input-group-sm" style={{ maxWidth: '120px' }}>
                          <button
                            className="btn btn-outline-secondary"
                            type="button"
                            onClick={() => handleDecrement(item.id, item.quantity)}
                            disabled={updatingItems[item.id] || loading}
                          >
                            {updatingItems[item.id] ? (
                              <span className="spinner-border spinner-border-sm" style={{ width: '1rem', height: '1rem' }} />
                            ) : (
                              <i className="bi bi-dash"></i>
                            )}
                          </button>
                          <input
                            type="text"
                            className="form-control text-center"
                            value={updatingItems[item.id] ? '...' : item.quantity}
                            readOnly
                            style={{ backgroundColor: 'white' }}
                          />
                          <button
                            className="btn btn-outline-secondary"
                            type="button"
                            onClick={() => handleIncrement(
                              item.id,
                              item.quantity,
                              item.max_cart_quantity || 20
                            )}
                            disabled={updatingItems[item.id] || loading || item.quantity >= (item.max_cart_quantity || 20)}
                          >
                            {updatingItems[item.id] ? (
                              <span className="spinner-border spinner-border-sm" style={{ width: '1rem', height: '1rem' }} />
                            ) : (
                              <i className="bi bi-plus"></i>
                            )}
                          </button>
                        </div>
                      </div>
                      <div className="col-md-2">
                        <span className="fw-bold d-block mb-2">
                          {frontendSettings.currency_symbol}{item.total_price || (item.product_price * item.quantity)}
                        </span>
                        <button
                          className="btn btn-outline-danger btn-sm"
                          onClick={() => showRemoveConfirmation(item.id)}
                          disabled={loading}
                        >
                          <i className="bi bi-trash"></i> Remove
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
                  <span>Subtotal ({cart.total_items} items):</span>
                  <span>{frontendSettings.currency_symbol}{cart.subtotal || cart.total}</span>
                </div>
                <div className="d-flex justify-content-between mb-2">
                  <span>Shipping:</span>
                  <span className="text-success">
                    {cart.subtotal >= (frontendSettings.free_shipping_min_amount || 500)
                      ? 'FREE'
                      : `Calculated at checkout`
                    }
                  </span>
                </div>
                {cart.subtotal < (frontendSettings.free_shipping_min_amount || 500) && (
                  <div className="alert alert-info py-2 mb-3">
                    <small>
                      Add {frontendSettings.currency_symbol}
                      {(frontendSettings.free_shipping_min_amount || 500) - cart.subtotal}
                      more for free shipping!
                    </small>
                  </div>
                )}
                <hr />
                <div className="d-flex justify-content-between mb-3">
                  <strong>Total:</strong>
                  <strong>{frontendSettings.currency_symbol}{cart.subtotal || cart.total}</strong>
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