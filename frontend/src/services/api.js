import axios from 'axios';

const createApiInstance = (baseURL) => {
  const instance = axios.create({
    baseURL,
    withCredentials: true, // This is crucial for cookies
  });

  instance.interceptors.request.use(
    (config) => {
      console.log(`🚀 Making ${config.method?.toUpperCase()} request to: ${config.url}`);
      console.log(`🍪 Current cookies:`, document.cookie);
      
      // Ensure withCredentials is always true
      config.withCredentials = true;
      
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
        console.log(`🔐 Using auth token`);
      } else {
        console.log(`👤 Guest user - relying on session cookie`);
      }

      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Add response interceptor to handle session cookies
  instance.interceptors.response.use(
    (response) => {
      // Log any set-cookie headers from response
      if (response.headers['set-cookie']) {
        console.log('🍪 Server set cookies in response:', response.headers['set-cookie']);
      }
      return response;
    },
    (error) => {
      console.error('❌ API Error:', error);
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