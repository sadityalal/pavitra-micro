import { db } from '../shared/database'; // This would be your database service

export const siteSettingsService = {
  async getSiteSettings() {
    try {
      // Since you have a shared config that reads from site_settings table
      // We'll create an API endpoint to get these settings
      const response = await fetch('/api/site-settings');
      if (!response.ok) {
        throw new Error('Failed to fetch site settings');
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching site settings:', error);
      // Return default values as fallback
      return this.getDefaultSettings();
    }
  },

  getDefaultSettings() {
    return {
      site_name: 'Pavitra Trading',
      site_description: 'Your trusted online shopping destination in India',
      currency: 'INR',
      currency_symbol: '₹',
      default_gst_rate: 18.00,
      enable_guest_checkout: true,
      maintenance_mode: false,
      enable_reviews: true,
      enable_wishlist: true,
      min_order_amount: 0.00,
      free_shipping_min_amount: 500.00,
      default_currency: 'INR',
      supported_currencies: ['INR', 'USD', 'GBP', 'EUR'],
      default_country: 'IN',
      app_debug: false,
      log_level: 'INFO',
      cors_origins: ['http://localhost:3000', 'http://localhost:3001'],
      rate_limit_requests: 100,
      rate_limit_window: 900,
      razorpay_test_mode: true,
      stripe_test_mode: true,
      email_notifications: true,
      sms_notifications: true,
      push_notifications: true,
      app_name: 'Pavitra Trading',
      app_description: 'Your trusted online shopping destination in India',
      debug_mode: false,
      refund_policy_days: 30,
      auto_refund_enabled: true,
      refund_processing_fee: 0.00
    };
  }
};