import React, { useEffect, useState } from 'react';
import { apiService } from '../../services/api';

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await apiService.get('/api/v1/orders');
        setOrders(res.orders || res || []);
      } catch (e) {
        console.error('Failed to load orders', e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <div className="container py-5 text-center">Loading orders...</div>;
  if (!orders.length) return <div className="container py-5 text-center">No orders found</div>;

  return (
    <div className="container py-4">
      <h2>My Orders</h2>
      <div className="list-group">
        {orders.map(o => (
          <div key={o.id} className="list-group-item">
            <div className="d-flex justify-content-between">
              <div>
                <strong>Order #{o.id}</strong>
                <div className="small">{o.status} • {o.total_amount}</div>
              </div>
              <div>
                <a href={`/order/${o.id}`} className="btn btn-sm btn-outline-primary">View</a>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Orders;
