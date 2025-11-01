import axios from 'axios';

const createApiInstance = (baseURL) => {
  const instance = axios.create({
    baseURL,
    withCredentials: true,
    // Headers will be set automatically based on content type
  });

  instance.interceptors.request.use(
    (config) => {
      console.log(`Making ${config.method?.toUpperCase()} request to: ${config.url}`);

      // Add auth token if available
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }

      // For FormData, let browser set Content-Type automatically with boundary
      if (config.data instanceof FormData) {
        // Remove Content-Type to let browser set it with boundary
        delete config.headers['Content-Type'];
      }

      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  instance.interceptors.response.use(
    (response) => response,
    (error) => {
      console.error('API Error:', error.response?.data || error.message);

      // Handle 422 validation errors specifically
      if (error.response?.status === 422) {
        console.error('Validation Error Details:', error.response.data);
      }

      return Promise.reject(error);
    }
  );

  return instance;
};

export const authApi = createApiInstance(process.env.REACT_APP_AUTH_URL || 'http://localhost:8001');
export const userApi = createApiInstance(process.env.REACT_APP_USER_URL || 'http://localhost:8004');
export const productApi = createApiInstance(process.env.REACT_APP_PRODUCT_URL || 'http://localhost:8002');
export const orderApi = createApiInstance(process.env.REACT_APP_ORDER_URL || 'http://localhost:8003');
export const paymentApi = createApiInstance(process.env.REACT_APP_PAYMENT_URL || 'http://localhost:8005');

export default { authApi, userApi, productApi, orderApi, paymentApi };