import { orderApi } from './api';

export const orderService = {
  // Create order
  createOrder: async (orderData) => {
    const response = await orderApi.post('/api/v1/orders', orderData);
    return response.data;
  },

  // Get user orders
  getUserOrders: async () => {
    const response = await orderApi.get('/api/v1/orders');
    return response.data;
  },

  // Get order by ID
  getOrderById: async (orderId) => {
    const response = await orderApi.get(`/api/v1/orders/${orderId}`);
    return response.data;
  },

  // Cancel order
  cancelOrder: async (orderId) => {
    const response = await orderApi.put(`/api/v1/orders/${orderId}/cancel`);
    return response.data;
  },

  // Get order status
  getOrderStatus: async (orderId) => {
    const response = await orderApi.get(`/api/v1/orders/${orderId}/status`);
    return response.data;
  }
};
