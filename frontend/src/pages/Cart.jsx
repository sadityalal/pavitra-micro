import React, { useEffect, useState } from 'react';
import { cartService } from '../services/cartService';

const Cart = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        if (cartService && typeof cartService.getCart === 'function') {
          const res = await cartService.getCart();
          setItems(res.items || []);
        } else {
          // fallback: read localStorage
          const ls = localStorage.getItem('cart');
          setItems(ls ? JSON.parse(ls) : []);
        }
      } catch (e) {
        console.error('Failed to load cart', e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <div className="container py-5 text-center">Loading cart...</div>;

  if (!items.length) return <div className="container py-5 text-center">Your cart is empty</div>;

  return (
    <div className="container py-4">
      <h2>Your Cart</h2>
      <ul className="list-group">
        {items.map(i => (
          <li key={i.id} className="list-group-item d-flex justify-content-between align-items-center">
            <div>
              <strong>{i.name}</strong>
              <div className="small">Qty: {i.quantity}</div>
            </div>
            <div>{i.price}</div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Cart;
