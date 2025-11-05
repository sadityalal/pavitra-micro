import axios from 'axios';

class SessionManager {
  constructor() {
    this.sessionId = null;
  }

  setSession(sessionId) {
    this.sessionId = sessionId;
    if (sessionId) {
      localStorage.setItem('shared_session_id', sessionId);
    }
  }

  getSession() {
    return this.sessionId || localStorage.getItem('shared_session_id');
  }

  clearSession() {
    this.sessionId = null;
    localStorage.removeItem('shared_session_id');
  }
}

export const sessionManager = new SessionManager();

const createApiInstance = (servicePath = '') => {
  // Use relative path - nginx will handle routing
  const instance = axios.create({
    baseURL: `/api/v1${servicePath}`,
    withCredentials: true,
    timeout: 30000,
  });

  instance.interceptors.request.use(
    (config) => {
      // Add session ID to all requests
      const sharedSessionId = sessionManager.getSession();
      if (sharedSessionId) {
        config.headers['X-Session-ID'] = sharedSessionId;
      }

      // Add auth token if available
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }

      return config;
    },
    (error) => Promise.reject(error)
  );

  instance.interceptors.response.use(
    (response) => {
      // Capture session ID from response headers
      const sessionId = response.headers['x-session-id'] ||
                        response.headers['x-secure-session-id'];
      if (sessionId) {
        sessionManager.setSession(sessionId);
      }
      return response;
    },
    (error) => {
      if (error.response?.status === 401) {
        localStorage.removeItem('auth_token');
        window.dispatchEvent(new Event('authStateChanged'));
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