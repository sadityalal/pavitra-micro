import React, { useEffect, useState } from 'react';
import { userService } from '../services/userService';
import { apiService } from '../services/api';
import { useNavigate } from 'react-router-dom';

const Checkout = () => {
  const [cart, setCart] = useState({ items: [], subtotal: 0 });
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [placing, setPlacing] = useState(false);
  const [selectedAddress, setSelectedAddress] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const c = await userService.getCart();
        setCart(c || { items: [] });
        const a = await userService.getAddresses();
        setAddresses(a || []);
        if ((a || []).length) setSelectedAddress((a[0] && a[0].id) || null);
      } catch (e) {
        console.error('Failed to load checkout data', e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handlePlaceOrder = async () => {
    if (!selectedAddress) return alert('Select an address');
    setPlacing(true);
    try {
      const payload = {
        address_id: selectedAddress,
        payment_method: 'cod',
      };
      const res = await apiService.post('/api/v1/orders', payload);
      const orderId = res.id || res.order_id;
      navigate(`/order/${orderId}`);
    } catch (err) {
      console.error(err);
      alert('Failed to place order');
    } finally {
      setPlacing(false);
    }
  };

  if (loading) return <div className="container py-5 text-center">Loading checkout...</div>;

  return (
    <div className="container py-4">
      <h2>Checkout</h2>
      <div className="row">
        <div className="col-md-7">
          <h4>Shipping address</h4>
          {addresses.length ? (
            <div className="list-group mb-4">
              {addresses.map(a => (
                <label key={a.id} className="list-group-item">
                  <input type="radio" name="address" checked={selectedAddress === a.id} onChange={() => setSelectedAddress(a.id)} />
                  <span className="ms-2">{a.line1}, {a.city} {a.postal_code}</span>
                </label>
              ))}
            </div>
          ) : (
            <div className="alert alert-warning">No addresses found. Add one in your account.</div>
          )}

          <h4>Items</h4>
          <ul className="list-group mb-4">
            {cart.items.map(i => (
              <li key={i.id} className="list-group-item d-flex justify-content-between">
                <div>
                  <strong>{i.name}</strong>
                  <div className="small">Qty: {i.quantity}</div>
                </div>
                <div>{i.price}</div>
              </li>
            ))}
          </ul>
        </div>
        <div className="col-md-5">
          <div className="card">
            <div className="card-body">
              <h5>Order summary</h5>
              <div className="d-flex justify-content-between">
                <div>Subtotal</div>
                <div>{cart.subtotal}</div>
              </div>
              <hr />
              <button className="btn btn-primary w-100" onClick={handlePlaceOrder} disabled={placing}>{placing ? 'Placing...' : 'Place Order'}</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Checkout;
