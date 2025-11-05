import { orderApi } from './api';

export const orderService = {
  createOrder: async (orderData) => {
    const response = await orderApi.post('/', orderData);
    return response.data;
  },

  getUserOrders: async () => {
    const response = await orderApi.get('/');
    return response.data;
  },

  getOrderById: async (orderId) => {
    const response = await orderApi.get(`/${orderId}`);
    return response.data;
  },

  cancelOrder: async (orderId) => {
    const response = await orderApi.put(`/${orderId}/cancel`);
    return response.data;
  },

  getOrderStatus: async (orderId) => {
    const response = await orderApi.get(`/${orderId}/status`);
    return response.data;
  }
};