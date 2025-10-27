// frontend/src/context/AuthContext.js
import React, { createContext, useState, useContext, useEffect } from 'react';
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
  const [siteSettings, setSiteSettings] = useState({});

  useEffect(() => {
    initializeAuth();
    loadSiteSettings();
  }, []);

  const initializeAuth = async () => {
    try {
      if (authService.isAuthenticated()) {
        const userData = authService.getUserData();
        setUser({
          ...userData,
          isAuthenticated: true
        });
        
        // Try to refresh token
        try {
          await authService.refreshToken();
        } catch (error) {
          console.log('Token refresh failed, logging out');
          await authService.logout();
          setUser(null);
        }
      }
    } catch (error) {
      console.error('Auth initialization failed:', error);
      await authService.logout();
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const loadSiteSettings = async () => {
    try {
      const settings = await authService.getSiteSettings();
      setSiteSettings(settings);
    } catch (error) {
      console.error('Failed to load site settings:', error);
    }
  };

  const login = async (loginData) => {
    try {
      setLoading(true);
      const response = await authService.login(loginData);
      
      const userData = {
        isAuthenticated: true,
        roles: response.user_roles,
        permissions: response.user_permissions,
        token: response.access_token
      };
      
      setUser(userData);
      return response;
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData) => {
    try {
      setLoading(true);
      const response = await authService.register(userData);
      
      const newUser = {
        isAuthenticated: true,
        roles: response.user_roles,
        permissions: response.user_permissions,
        token: response.access_token
      };
      
      setUser(newUser);
      return response;
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      setLoading(true);
      await authService.logout();
      setUser(null);
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setLoading(false);
    }
  };

  const refreshSettings = async () => {
    await loadSiteSettings();
  };

  const value = {
    user,
    login,
    register,
    logout,
    loading,
    isAuthenticated: !!user?.isAuthenticated,
    siteSettings,
    refreshSettings
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};