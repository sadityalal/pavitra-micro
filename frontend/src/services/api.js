import axios from 'axios';

const createApiInstance = (basePath = '') => {
  const instance = axios.create({
    baseURL: `/api/v1${basePath}`, // This goes through nginx proxy
    withCredentials: true, // This is crucial for cookies
  });

  instance.interceptors.request.use(
    (config) => {
      console.log(`🚀 Making ${config.method?.toUpperCase()} request to: ${config.baseURL}${config.url}`);
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

  instance.interceptors.response.use(
    (response) => {
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

// Create API instances that match your nginx routes
export const authApi = createApiInstance('/auth');      // → /api/v1/auth/
export const userApi = createApiInstance('/users');     // → /api/v1/users/
export const productApi = createApiInstance('/products'); // → /api/v1/products/
export const orderApi = createApiInstance('/orders');   // → /api/v1/orders/
export const paymentApi = createApiInstance('/payments'); // → /api/v1/payments/

export default { authApi, userApi, productApi, orderApi, paymentApi };