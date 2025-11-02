import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const useSafeToast = () => {
  try {
    const { success, error } = useContext(require('./ToastContext').ToastContext);
    return { success, error };
  } catch (err) {
    return {
      success: (message) => console.log('✅', message),
      error: (message) => console.error('❌', message)
    };
  }
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const navigate = useNavigate();
  const { success, error } = useSafeToast();

  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const token = localStorage.getItem('auth_token');
        if (token) {
          setIsAuthenticated(true);
          setUser({
            id: 'user_id',
            email: 'user@example.com',
            roles: ['customer'],
            permissions: []
          });
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        localStorage.removeItem('auth_token');
      } finally {
        setLoading(false);
      }
    };
    checkAuthStatus();
  }, []);

  const login = async (credentials) => {
    try {
      setLoading(true);
      const response = await authService.login(credentials);
      if (response.access_token) {
        localStorage.setItem('auth_token', response.access_token);
        const userData = {
          id: 'user_id',
          email: credentials.login_id,
          roles: response.user_roles || [],
          permissions: response.user_permissions || []
        };
        setUser(userData);
        setIsAuthenticated(true);

        // Trigger cart refresh after login
        const cartEvent = new CustomEvent('authStateChanged', {
          detail: { action: 'login', user: userData }
        });
        document.dispatchEvent(cartEvent);

        success('Login successful! Welcome back.');
        return response;
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
      await authService.logout();
      success('You have been successfully logged out');

      // Clear cart state immediately
      const cartEvent = new CustomEvent('authStateChanged', {
        detail: { action: 'logout' }
      });
      document.dispatchEvent(cartEvent);

      setTimeout(() => {
        navigate('/');
      }, 500);
    } catch (err) {
      console.error('Logout error:', err);
      error('There was an issue during logout, but you have been logged out locally.');

      // Still clear cart state even if logout API fails
      const cartEvent = new CustomEvent('authStateChanged', {
        detail: { action: 'logout' }
      });
      document.dispatchEvent(cartEvent);

      localStorage.removeItem('auth_token');
      setUser(null);
      setIsAuthenticated(false);
      setTimeout(() => {
        navigate('/');
      }, 1500);
    } finally {
      localStorage.removeItem('auth_token');
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  const register = async (userData) => {
    try {
      setLoading(true);
      console.log('Registering user with data:', userData);
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

        // Trigger cart refresh after registration
        const cartEvent = new CustomEvent('authStateChanged', {
          detail: { action: 'register', user: userData }
        });
        document.dispatchEvent(cartEvent);

        success('Registration successful! Welcome to our platform.');
        return response;
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
      } else {
        error('Registration failed. Please try again.');
      }
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const forgotPassword = async (email) => {
    try {
      setLoading(true);
      await authService.forgotPassword(email);
      success('If the email exists, a password reset link has been sent.');
    } catch (err) {
      console.error('Forgot password failed:', err);
      error('Failed to send reset email. Please try again.');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const resetPassword = async (token, newPassword) => {
    try {
      setLoading(true);
      await authService.resetPassword(token, newPassword);
      success('Password reset successfully. You can now login with your new password.');
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

  const hasRole = (role) => {
    return user?.roles?.includes(role) || false;
  };

  const hasPermission = (permission) => {
    return user?.permissions?.includes(permission) || false;
  };

  const isAdmin = () => {
    return hasRole('admin') || hasRole('super_admin');
  };

  const refreshUser = async () => {
    // Implementation for refreshing user data
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
    hasRole,
    hasPermission,
    isAdmin,
    refreshUser
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};