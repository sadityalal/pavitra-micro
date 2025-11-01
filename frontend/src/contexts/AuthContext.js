// frontend/src/contexts/AuthContext.js
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

  // Check if user is logged in on app start
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const token = localStorage.getItem('auth_token');
        if (token) {
          // Verify token and get user data
          // This would typically call an endpoint to verify token
          // For now, we'll set a basic authenticated state
          setIsAuthenticated(true);
          // You would fetch user profile here
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
          id: response.user_id,
          email: credentials.login_id,
          roles: response.user_roles || [],
          permissions: response.user_permissions || []
        });
        setIsAuthenticated(true);
        return response;
      }
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
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
      const response = await authService.register(userData);
      
      if (response.access_token) {
        localStorage.setItem('auth_token', response.access_token);
        setUser({
          id: response.user_id,
          email: userData.email,
          roles: response.user_roles || ['customer'],
          permissions: response.user_permissions || []
        });
        setIsAuthenticated(true);
        return response;
      }
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
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
    refreshUser: () => {
      // Implement user data refresh if needed
    }
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};