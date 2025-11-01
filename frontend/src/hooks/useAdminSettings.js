import { useState, useEffect } from 'react';
import { authService } from '../services/authService';
import { useAuth } from '../contexts/AuthContext';

export const useAdminSettings = () => {
  const [siteSettings, setSiteSettings] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { isAdmin } = useAuth();

  const fetchSiteSettings = async () => {
    if (!isAdmin()) {
      setError('Access denied: Admin role required');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const settings = await authService.getSiteSettings();
      setSiteSettings(settings);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const updateSiteSettings = async (updatedSettings) => {
    if (!isAdmin()) {
      throw new Error('Access denied: Admin role required');
    }

    try {
      setLoading(true);
      setError(null);
      const result = await authService.updateSiteSettings(updatedSettings);
      setSiteSettings(updatedSettings);
      return result;
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAdmin()) {
      fetchSiteSettings();
    }
  }, [isAdmin]);

  return {
    siteSettings,
    loading,
    error,
    fetchSiteSettings,
    updateSiteSettings,
    canAccess: isAdmin()
  };
};
