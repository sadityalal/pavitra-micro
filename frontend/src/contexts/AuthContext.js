import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import { sessionManager } from '../services/api';

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
          try {
            const userProfile = await authService.getSiteSettings().catch(() => null);
            if (userProfile) {
              setIsAuthenticated(true);
              setUser({
                id: 'user_id',
                email: 'user@example.com',
                roles: ['customer'],
                permissions: []
              });
              console.log('✅ User authenticated from stored token');
            } else {
              localStorage.removeItem('auth_token');
              sessionManager.clearSession();
              console.log('❌ Stored token is invalid, clearing auth state');
            }
          } catch (verifyError) {
            console.error('Token verification failed:', verifyError);
            localStorage.removeItem('auth_token');
            sessionManager.clearSession();
          }
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        localStorage.removeItem('auth_token');
        sessionManager.clearSession();
      } finally {
        setLoading(false);
      }
    };
    checkAuthStatus();
  }, []);

  // In frontend/src/contexts/AuthContext.js - Update the login function

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
      sessionManager.clearSession();

      console.log('✅ Login successful, attempting cart migration...');

      try {
        const migrationResponse = await fetch('/api/v1/users/cart/migrate-guest-to-user', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${response.access_token}`,
            'Content-Type': 'application/json',
          },
          credentials: 'include'
        });

        if (migrationResponse.ok) {
          const migrationResult = await migrationResponse.json();
          console.log('🔄 Cart migration result:', migrationResult);

          if (migrationResult.success && migrationResult.items_migrated > 0) {
            success(`Cart migrated successfully! ${migrationResult.items_migrated} items added to your account.`);
          } else if (migrationResult.success) {
            console.log('🔄 Cart migration successful but no items to migrate');
          } else {
            console.warn('🔄 Cart migration failed:', migrationResult.message);
          }
        } else {
          console.warn('🔄 Cart migration endpoint returned:', migrationResponse.status);
          // Don't show error to user - this is not critical
        }
      } catch (migrationError) {
        console.warn('🔄 Cart migration failed, but login was successful:', migrationError);
        // Don't show error to user - this is not critical
      }

      console.log('✅ Login successful, guest session cleared');

      const cartEvent = new CustomEvent('authStateChanged', {
        detail: {
          action: 'login',
          user: userData,
          sessionType: 'authenticated'
        }
      });
      document.dispatchEvent(cartEvent);

      success('Login successful! Welcome back.');
      return response;
    } else {
      throw new Error('No access token received from server');
    }
  } catch (err) {
    console.error('❌ Login failed:', err);
    if (err.response?.data?.detail) {
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
      success('You have been successfully logged out');
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
      const userProfile = {
        id: 'user_id',
        email: userData.email || userData.phone || userData.username,
        first_name: userData.first_name,
        last_name: userData.last_name,
        roles: response.user_roles || ['customer'],
        permissions: response.user_permissions || []
      };

      setUser(userProfile);
      setIsAuthenticated(true);
      sessionManager.clearSession();

      console.log('✅ Registration successful, attempting cart migration...');

      // Call explicit cart migration after successful registration
      try {
        const migrationResponse = await fetch('/api/v1/users/cart/migrate-guest-to-user', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${response.access_token}`,
            'Content-Type': 'application/json',
          },
          credentials: 'include'
        });

        if (migrationResponse.ok) {
          const migrationResult = await migrationResponse.json();
          console.log('🔄 Cart migration result:', migrationResult);
          if (migrationResult.items_migrated > 0) {
            success(`Registration successful! ${migrationResult.items_migrated} cart items migrated to your account.`);
          } else {
            success('Registration successful! Welcome to our platform.');
          }
        }
      } catch (migrationError) {
        console.warn('Cart migration failed, but registration was successful:', migrationError);
        success('Registration successful! Welcome to our platform.');
      }

      console.log('✅ Registration successful, guest session cleared');

      const cartEvent = new CustomEvent('authStateChanged', {
        detail: {
          action: 'register',
          user: userProfile,
          sessionType: 'authenticated'
        }
      });
      document.dispatchEvent(cartEvent);

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
      const detail = err.response.data.detail;
      if (typeof detail === 'string') {
        error(detail);
      } else {
        error('Email, phone, or username already exists. Please use different credentials.');
      }
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

  const forgotPassword = async (email) => {
    try {
      setLoading(true);
      console.log('🔑 Requesting password reset for:', email);
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
      console.log('🔑 Resetting password with token');
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
    try {
      console.log('🔄 Refreshing user data...');
      return user;
    } catch (error) {
      console.error('Failed to refresh user:', error);
      throw error;
    }
  };

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