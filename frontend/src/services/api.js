import axios from 'axios';

const createApiInstance = (baseURL) => {
  const instance = axios.create({
    baseURL,
    withCredentials: true, // THIS IS CRITICAL - ensures cookies are sent
  });

  instance.interceptors.request.use(
    (config) => {
      console.log(`🚀 Making ${config.method?.toUpperCase()} request to: ${config.url}`);
      console.log(`🍪 Cookies being sent:`, document.cookie);

      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
        console.log(`🔐 Using auth token`);
      } else {
        console.log(`👤 Guest user - relying on session cookie`);
      }

      // Double ensure credentials are included
      config.withCredentials = true;

      if (config.data instanceof FormData) {
        delete config.headers['Content-Type'];
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  instance.interceptors.response.use(
    (response) => {
      console.log(`✅ Response received from: ${response.config.url}`);
      // Check if response has set-cookie headers
      if (response.headers['set-cookie']) {
        console.log(`🍪 Server set cookies:`, response.headers['set-cookie']);
      }
      return response;
    },
    (error) => {
      console.error('❌ API Error:', error);
      console.error('❌ Error response:', error.response?.data);
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