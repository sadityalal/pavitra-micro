import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { apiService } from '../services/api';

const OrderConfirmation = () => {
  const { id } = useParams();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await apiService.get(`/api/v1/orders/${id}`);
        setOrder(res || null);
      } catch (e) {
        console.error('Failed to load order', e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  if (loading) return <div className="container py-5 text-center">Loading order...</div>;
  if (!order) return <div className="container py-5 text-center">Order not found</div>;

  return (
    <div className="container py-4">
      <h2>Order #{order.id}</h2>
      <p>Status: {order.status}</p>
      <h5>Items</h5>
      <ul className="list-group mb-3">
        {order.items?.map(i => (
          <li key={i.id} className="list-group-item d-flex justify-content-between">
            <div>{i.name} <div className="small">Qty: {i.quantity}</div></div>
            <div>{i.price}</div>
          </li>
        ))}
      </ul>
      <div className="alert alert-success">Thank you for your order.</div>
    </div>
  );
};

export default OrderConfirmation;
