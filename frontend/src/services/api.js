import axios from 'axios';

// Create a shared session manager
class SessionManager {
  constructor() {
    this.sessionId = null;
  }

  setSession(sessionId) {
    this.sessionId = sessionId;
    // Also store in localStorage as backup
    if (sessionId) {
      localStorage.setItem('shared_session_id', sessionId);
      console.log('💾 Stored session ID:', sessionId);
    } else {
      localStorage.removeItem('shared_session_id');
    }
  }

  getSession() {
    return this.sessionId || localStorage.getItem('shared_session_id');
  }

  clearSession() {
    this.sessionId = null;
    localStorage.removeItem('shared_session_id');
    console.log('🧹 Cleared session ID');
  }
}

export const sessionManager = new SessionManager();

const createApiInstance = (basePath = '') => {
  const instance = axios.create({
    baseURL: `/api/v1${basePath}`,
    withCredentials: true, // Crucial for cookies
  });

  instance.interceptors.request.use(
    (config) => {
      console.log(`🚀 Making ${config.method?.toUpperCase()} request to: ${config.baseURL}${config.url}`);

      // Ensure withCredentials is always true for session cookies
      config.withCredentials = true;

      // Add shared session ID to headers for ALL services
      const sharedSessionId = sessionManager.getSession();
      if (sharedSessionId) {
        config.headers['X-Session-ID'] = sharedSessionId;
        console.log(`🔗 Using shared session: ${sharedSessionId}`);
      }

      // Add auth token if available
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
        console.log(`🔐 Using auth token`);
      } else {
        console.log(`👤 Guest user - using session only`);
      }

      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  instance.interceptors.response.use(
    (response) => {
      // Capture session ID from response headers if present
      const sessionId = response.headers['x-session-id'];
      if (sessionId) {
        sessionManager.setSession(sessionId);
        console.log('🆕 Received session ID from server:', sessionId);
      }

      return response;
    },
    (error) => {
      console.error('❌ API Error:', error);

      // Handle session-related errors
      if (error.response?.status === 401 || error.response?.status === 419) {
        console.log('🔐 Session expired or invalid');
        sessionManager.clearSession();
      }

      return Promise.reject(error);
    }
  );

  return instance;
};

export const authApi = createApiInstance('/auth');
export const userApi = createApiInstance('/users');
export const productApi = createApiInstance('/products');
export const orderApi = createApiInstance('/orders');
export const paymentApi = createApiInstance('/payments');

export default { authApi, userApi, productApi, orderApi, paymentApi, sessionManager };