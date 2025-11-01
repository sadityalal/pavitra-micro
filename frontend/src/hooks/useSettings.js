import { useState, useEffect } from 'react';
import { authService } from '../services/authService';

export const useSettings = () => {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        setLoading(true);
        const frontendSettings = await authService.getFrontendSettings();
        setSettings(frontendSettings);
      } catch (err) {
        setError(err.message);
        // Fallback to default settings if API fails
        setSettings(getDefaultSettings());
      } finally {
        setLoading(false);
      }
    };

    fetchSettings();
  }, []);

  return { settings, loading, error };
};

// Default settings fallback
const getDefaultSettings = () => ({
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
