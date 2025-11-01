// frontend/src/contexts/SettingsContext.js
import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';
import { useAuth } from './AuthContext';

const SettingsContext = createContext();

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};

export const SettingsProvider = ({ children }) => {
  const [frontendSettings, setFrontendSettings] = useState({});
  const [siteSettings, setSiteSettings] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { isAuthenticated, isAdmin } = useAuth();

  // Fetch public frontend settings (no auth required)
  const fetchFrontendSettings = async () => {
    try {
      setLoading(true);
      setError(null);

      const frontendSettingsData = await authService.getFrontendSettings();
      setFrontendSettings(frontendSettingsData);

    } catch (err) {
      console.error('Failed to fetch frontend settings:', err);
      setError(err.message);
      // Fallback to default frontend settings
      setFrontendSettings(getDefaultFrontendSettings());
    } finally {
      setLoading(false);
    }
  };

  // Fetch admin site settings (requires authentication and admin role)
  const fetchSiteSettings = async () => {
    if (!isAuthenticated || !isAdmin()) {
      console.log('Skipping site settings fetch - user not admin');
      return;
    }

    try {
      const siteSettingsData = await authService.getSiteSettings();
      setSiteSettings(siteSettingsData);
    } catch (err) {
      console.error('Failed to fetch site settings:', err);
      // Don't set error for site settings since it's admin-only
    }
  };

  // Refresh all settings
  const refreshSettings = async () => {
    await fetchFrontendSettings();
    if (isAuthenticated && isAdmin()) {
      await fetchSiteSettings();
    }
  };

  useEffect(() => {
    fetchFrontendSettings();
  }, []);

  // Fetch site settings when user becomes admin
  useEffect(() => {
    if (isAuthenticated && isAdmin()) {
      fetchSiteSettings();
    }
  }, [isAuthenticated, isAdmin]);

  const value = {
    // Public frontend settings for all users
    frontendSettings,

    // Admin-only site settings (empty object for non-admins)
    siteSettings,

    // Combined settings for backward compatibility (only frontend settings for public)
    settings: frontendSettings,

    loading,
    error,

    // Refresh functions
    refreshFrontendSettings: fetchFrontendSettings,
    refreshSiteSettings: fetchSiteSettings,
    refreshSettings,

    // Helper to check if user can access admin settings
    canAccessAdminSettings: isAuthenticated && isAdmin()
  };

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
};

const getDefaultFrontendSettings = () => ({
  site_name: 'Pavitra Trading',
  currency: 'INR',
  currency_symbol: '₹',
  min_order_amount: 0,
  free_shipping_min_amount: 500,
  free_shipping_threshold: 999,
  return_period_days: 10,
  enable_reviews: true,
  enable_wishlist: true,
  enable_guest_checkout: true,
  site_phone: '+91-9711317009',
  site_email: 'support@pavitraenterprises.com',
  business_hours: {
    monday_friday: '9am-6pm',
    saturday: '10am-4pm',
    sunday: 'Closed'
  }
});