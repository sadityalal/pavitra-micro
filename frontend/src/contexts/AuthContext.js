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
          // You might want to validate the token with the backend here
          setIsAuthenticated(true);
          // Set basic user info from token (you might need to decode JWT)
          setUser({
            id: 'user_id_from_token', // This should be extracted from token
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