// frontend/src/contexts/AuthContext.js
import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import { sessionManager } from '../services/api';
import { useToast } from '../contexts/ToastContext';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const navigate = useNavigate();
  const { success, error } = useToast();

  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const token = localStorage.getItem('auth_token');
        if (token) {
          try {
            // Verify token is valid by making a simple API call
            const userProfile = await authService.getFrontendSettings();
            if (userProfile) {
              setIsAuthenticated(true);
              setUser({
                id: 'user_id',
                email: 'user@example.com',
                roles: ['customer'],
                permissions: []
              });
              console.log('✅ User authenticated from stored token');
            }
          } catch (verifyError) {
            console.error('Token verification failed:', verifyError);
            localStorage.removeItem('auth_token');
            sessionManager.clearSession();
          }
        }
      } catch (error) {
        console.error('Auth check failed:', error);
      } finally {
        setLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  const login = async (credentials) => {
    try {
      setLoading(true);
      console.log('🔐 Attempting login with credentials:', {
        login_id: credentials.login_id,
        password_length: credentials.password ? credentials.password.length : 0
      });

      const response = await authService.login(credentials);

      if (response.access_token) {
        localStorage.setItem('auth_token', response.access_token);

        const userData = {
          id: 'user_id',
          email: credentials.login_id,
          first_name: response.user?.first_name,
          last_name: response.user?.last_name,
          roles: response.user_roles || ['customer'],
          permissions: response.user_permissions || []
        };

        setUser(userData);
        setIsAuthenticated(true);

        // Trigger cart migration event
        const cartEvent = new CustomEvent('authStateChanged', {
          detail: {
            action: 'login',
            user: userData,
            sessionType: 'authenticated'
          }
        });
        document.dispatchEvent(cartEvent);

        success('Login successful! Welcome back.', 3000);
        return response;
      } else {
        throw new Error('No access token received from server');
      }
    } catch (err) {
      console.error('Login failed:', err);
      if (err.response?.status === 401) {
        error('Invalid credentials. Please check your email/username and password.');
      } else if (err.response?.status === 422) {
        error('Invalid input format. Please check your data.');
      } else if (err.response?.status === 429) {
        error('Too many login attempts. Please try again later.');
      } else if (err.response?.status === 503) {
        error('Service is under maintenance. Please try again later.');
      } else if (err.response?.data?.detail) {
        error(err.response.data.detail);
      } else if (err.message) {
        error(err.message);
      } else {
        error('Login failed. Please try again.');
      }
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      console.log('🔐 Logging out user...');
      await authService.logout();
      success('You have been successfully logged out', 3000);
    } catch (err) {
      console.error('Logout API call failed:', err);
      error('There was an issue during logout, but you have been logged out locally.');
    } finally {
      localStorage.removeItem('auth_token');
      sessionManager.clearSession();
      setUser(null);
      setIsAuthenticated(false);

      console.log('✅ Local auth state cleared');
      const cartEvent = new CustomEvent('authStateChanged', {
        detail: {
          action: 'logout',
          sessionType: 'guest'
        }
      });
      document.dispatchEvent(cartEvent);

      setTimeout(() => {
        navigate('/');
      }, 500);
    }
  };

  const register = async (userData) => {
    try {
      setLoading(true);
      console.log('👤 Registering user with data:', {
        first_name: userData.first_name,
        last_name: userData.last_name,
        email: userData.email,
        phone: userData.phone,
        username: userData.username
      });

      const response = await authService.register(userData);

      if (response.access_token) {
        localStorage.setItem('auth_token', response.access_token);

        const userData = {
          id: 'user_id',
          email: userData.email,
          first_name: userData.first_name,
          last_name: userData.last_name,
          roles: response.user_roles || ['customer'],
          permissions: response.user_permissions || []
        };

        setUser(userData);
        setIsAuthenticated(true);

        // Trigger cart migration event
        const cartEvent = new CustomEvent('authStateChanged', {
          detail: {
            action: 'register',
            user: userData,
            sessionType: 'authenticated'
          }
        });
        document.dispatchEvent(cartEvent);

        success('Registration successful! Welcome to our platform.', 3000);
        return response;
      } else {
        throw new Error('No access token received from server');
      }
    } catch (err) {
      console.error('Registration failed:', err);
      if (err.response?.status === 422) {
        const validationErrors = err.response.data.detail;
        if (Array.isArray(validationErrors)) {
          const errorMessages = validationErrors.map(err => err.msg || err).join(', ');
          error(`Validation failed: ${errorMessages}`);
        } else if (typeof validationErrors === 'string') {
          error(validationErrors);
        } else if (validationErrors && typeof validationErrors === 'object') {
          const errorMessage = Object.values(validationErrors).flat().join(', ');
          error(`Validation failed: ${errorMessage}`);
        }
      } else if (err.response?.data?.detail) {
        error(err.response.data.detail);
      } else if (err.response?.status === 400) {
        error('Email, phone, or username already exists. Please use different credentials.');
      } else if (err.response?.status === 503) {
        error('Service is under maintenance. Registration is temporarily unavailable.');
      } else if (err.message) {
        error(err.message);
      } else {
        error('Registration failed. Please try again.');
      }
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // FORGOT PASSWORD FUNCTION - PRESERVED
  const forgotPassword = async (email) => {
    try {
      setLoading(true);
      console.log('🔑 Requesting password reset for:', email);
      await authService.forgotPassword(email);
      success('If the email exists, a password reset link has been sent.', 5000);
    } catch (err) {
      console.error('Forgot password failed:', err);
      error('Failed to send reset email. Please try again.');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // RESET PASSWORD FUNCTION - PRESERVED
  const resetPassword = async (token, newPassword) => {
    try {
      setLoading(true);
      console.log('🔑 Resetting password with token');
      await authService.resetPassword(token, newPassword);
      success('Password reset successfully. You can now login with your new password.', 5000);
    } catch (err) {
      console.error('Reset password failed:', err);
      if (err.response?.status === 400) {
        error('Invalid or expired reset token.');
      } else {
        error('Failed to reset password. Please try again.');
      }
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // REFRESH TOKEN FUNCTION - PRESERVED
  const refreshToken = async () => {
    try {
      console.log('🔄 Refreshing token...');
      const response = await authService.refreshToken();
      if (response.access_token) {
        localStorage.setItem('auth_token', response.access_token);
        return response;
      }
      throw new Error('No access token received');
    } catch (err) {
      console.error('Token refresh failed:', err);
      throw err;
    }
  };

  // CHECK PERMISSION FUNCTION - PRESERVED
  const checkPermission = async (permission) => {
    try {
      const response = await authService.checkPermission(permission);
      return response.has_access;
    } catch (err) {
      console.error('Permission check failed:', err);
      return false;
    }
  };

  // GET ROLES FUNCTION - PRESERVED
  const getRoles = async () => {
    try {
      return await authService.getRoles();
    } catch (err) {
      console.error('Failed to fetch roles:', err);
      return [];
    }
  };

  // ROLE AND PERMISSION CHECK FUNCTIONS - PRESERVED
  const hasRole = (role) => {
    return user?.roles?.includes(role) || false;
  };

  const hasPermission = (permission) => {
    return user?.permissions?.includes(permission) || false;
  };

  const isAdmin = () => {
    return hasRole('admin') || hasRole('super_admin');
  };

  // REFRESH USER FUNCTION - PRESERVED
  const refreshUser = async () => {
    try {
      console.log('🔄 Refreshing user data...');
      // In a real implementation, this would fetch fresh user data from the server
      return user;
    } catch (error) {
      console.error('Failed to refresh user:', error);
      throw error;
    }
  };

  // GET AUTH HEADERS FUNCTION - PRESERVED
  const getAuthHeaders = () => {
    const headers = {};
    const token = localStorage.getItem('auth_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const sessionId = sessionManager.getSession();
    if (sessionId) {
      headers['X-Session-ID'] = sessionId;
    }
    return headers;
  };

  // GET SESSION INFO FUNCTION - PRESERVED
  const getSessionInfo = async () => {
    try {
      const response = await fetch('/api/v1/users/session/info', {
        credentials: 'include',
        headers: getAuthHeaders()
      });
      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.error('Failed to get session info:', error);
      return null;
    }
  };

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    logout,
    register,
    forgotPassword,
    resetPassword,
    refreshToken,
    checkPermission,
    getRoles,
    hasRole,
    hasPermission,
    isAdmin,
    refreshUser,
    getAuthHeaders,
    getSessionInfo
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};