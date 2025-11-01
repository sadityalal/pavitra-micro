import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';

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

  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const token = localStorage.getItem('auth_token');
        if (token) {
          setIsAuthenticated(true);
          // For now, set basic user info - you might want to fetch user profile
          setUser({
            id: 'user_id', // This should come from token or API call
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

        setUser({
          id: 'user_id', // This should come from backend response
          email: credentials.login_id,
          roles: response.user_roles || [],
          permissions: response.user_permissions || []
        });

        setIsAuthenticated(true);
        return response;
      }
    } catch (error) {
      console.error('Login failed:', error);

      // Provide better error messages
      if (error.response?.status === 401) {
        throw new Error('Invalid credentials. Please check your email/username and password.');
      } else if (error.response?.status === 422) {
        throw new Error('Invalid input format. Please check your data.');
      } else {
        throw new Error('Login failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
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

        setUser({
          id: 'user_id', // This should come from backend response
          email: userData.email,
          first_name: userData.first_name,
          last_name: userData.last_name,
          roles: response.user_roles || ['customer'],
          permissions: response.user_permissions || []
        });

        setIsAuthenticated(true);
        return response;
      }
    } catch (error) {
      console.error('Registration failed:', error);

      // Provide detailed error messages for 422 validation errors
      if (error.response?.status === 422) {
        const validationErrors = error.response.data.detail;
        if (Array.isArray(validationErrors)) {
          const errorMessages = validationErrors.map(err => err.msg || err).join(', ');
          throw new Error(`Validation failed: ${errorMessages}`);
        } else if (typeof validationErrors === 'string') {
          throw new Error(validationErrors);
        } else if (validationErrors && typeof validationErrors === 'object') {
          const errorMessage = Object.values(validationErrors).flat().join(', ');
          throw new Error(`Validation failed: ${errorMessage}`);
        }
      } else if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      } else {
        throw new Error('Registration failed. Please try again.');
      }
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
    // Implement user data refresh if needed
  };

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    logout,
    register,
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