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

  async ensureGuestSession() {
    if (!this.getSession() && !localStorage.getItem('auth_token')) {
      try {
        console.log('🔄 Ensuring guest session...');
        const response = await fetch('/api/v1/users/health', {
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        const sessionId = response.headers.get('x-session-id') ||
                         response.headers.get('x-secure-session-id');
        if (sessionId) {
          this.setSession(sessionId);
          console.log('✅ Guest session ensured:', sessionId);
        }
        return true;
      } catch (error) {
        console.error('❌ Failed to ensure guest session:', error);
        return false;
      }
    }
    return true;
  }
}

export const sessionManager = new SessionManager();

const createApiInstance = (servicePath = '') => {
  const instance = axios.create({
    baseURL: `/api/v1${servicePath}`,
    withCredentials: true, // This is CRITICAL for cookies
    timeout: 30000,
  });

  instance.interceptors.request.use(
    (config) => {
      const sharedSessionId = sessionManager.getSession();
      const token = localStorage.getItem('auth_token');

      // Always include session headers
      if (sharedSessionId) {
        config.headers['X-Session-ID'] = sharedSessionId;
        config.headers['X-Secure-Session-ID'] = sharedSessionId;
      }

      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }

      // Ensure cookies are sent
      config.withCredentials = true;

      return config;
    },
    (error) => Promise.reject(error)
  );

  instance.interceptors.response.use(
    (response) => {
      // Check for session ID in cookies from response
      const setCookieHeader = response.headers['set-cookie'];
      if (setCookieHeader) {
        console.log('🍪 Set-Cookie header:', setCookieHeader);
      }

      const sessionId = response.headers['x-session-id'] ||
                        response.headers['x-secure-session-id'];
      if (sessionId) {
        sessionManager.setSession(sessionId);
        console.log('🔄 Session updated from response:', sessionId);
      }
      return response;
    },
    (error) => {
      console.error('🔗 API Error:', error.response?.status, error.message);
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