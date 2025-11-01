import { paymentApi } from './api';

export const paymentService = {
  // Create payment
  createPayment: async (paymentData) => {
    const response = await paymentApi.post('/api/v1/payments', paymentData);
    return response.data;
  },

  // Process payment
  processPayment: async (paymentId, paymentMethod) => {
    const response = await paymentApi.post(`/api/v1/payments/${paymentId}/process`, {
      payment_method: paymentMethod
    });
    return response.data;
  },

  // Get payment status
  getPaymentStatus: async (paymentId) => {
    const response = await paymentApi.get(`/api/v1/payments/${paymentId}/status`);
    return response.data;
  },

  // Refund payment
  refundPayment: async (paymentId, amount) => {
    const response = await paymentApi.post(`/api/v1/payments/${paymentId}/refund`, {
      amount
    });
    return response.data;
  }
};
