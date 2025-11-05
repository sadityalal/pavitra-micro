import { paymentApi } from './api';

export const paymentService = {
  createPayment: async (paymentData) => {
    const response = await paymentApi.post('/', paymentData);
    return response.data;
  },

  processPayment: async (paymentId, paymentMethod) => {
    const response = await paymentApi.post(`/${paymentId}/process`, {
      payment_method: paymentMethod
    });
    return response.data;
  },

  getPaymentStatus: async (paymentId) => {
    const response = await paymentApi.get(`/${paymentId}/status`);
    return response.data;
  },

  refundPayment: async (paymentId, amount) => {
    const response = await paymentApi.post(`/${paymentId}/refund`, {
      amount
    });
    return response.data;
  }
};