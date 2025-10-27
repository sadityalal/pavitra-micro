import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../services/api';

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
    const token = localStorage.getItem('authToken');
    if (token) {
      try {
        const userProfile = await api.getUserProfile();
        setUser(userProfile);
      } catch (error) {
        console.error('Failed to get user profile:', error);
        localStorage.removeItem('authToken');
      }
    }
    setLoading(false);
  };

  const loadSiteSettings = async () => {
    try {
      const settings = await api.getSiteSettings();
      setSiteSettings(settings);
    } catch (error) {
      console.error('Failed to load site settings:', error);
    }
  };

  const login = async (loginData) => {
    try {
      const response = await api.login(loginData);
      
      if (response.access_token) {
        localStorage.setItem('authToken', response.access_token);
        
        // Get user profile after login
        const userProfile = await api.getUserProfile();
        setUser(userProfile);
        
        return { success: true, user: userProfile };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const register = async (userData) => {
    try {
      const response = await api.register(userData);
      
      if (response.access_token) {
        localStorage.setItem('authToken', response.access_token);
        
        // Get user profile after registration
        const userProfile = await api.getUserProfile();
        setUser(userProfile);
        
        return { success: true, user: userProfile };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const logout = async () => {
    try {
      await api.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('authToken');
      setUser(null);
    }
  };

  const updateUser = (userData) => {
    setUser(prevUser => ({ ...prevUser, ...userData }));
  };

  const value = {
    user,
    loading,
    siteSettings,
    login,
    register,
    logout,
    updateUser,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
