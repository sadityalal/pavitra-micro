-- Development configuration with test values
-- Update existing settings with development values

-- Razorpay Test Credentials (Get from Razorpay Test Dashboard)
UPDATE site_settings SET setting_value = 'rzp_test_xxxxxxxxxxxx' WHERE setting_key = 'razorpay_key_id';
UPDATE site_settings SET setting_value = 'razorpay_test_secret_xxxx' WHERE setting_key = 'razorpay_secret';

-- Stripe Test Credentials (Get from Stripe Test Dashboard)
UPDATE site_settings SET setting_value = 'sk_test_xxxxxxxxxxxxxxxxxxxx' WHERE setting_key = 'stripe_secret_key';
UPDATE site_settings SET setting_value = 'pk_test_xxxxxxxxxxxxxxxxxxxx' WHERE setting_key = 'stripe_publishable_key';

-- PayPal Sandbox Credentials
UPDATE site_settings SET setting_value = 'AeA**********************_w' WHERE setting_key = 'paypal_client_id';
UPDATE site_settings SET setting_value = 'EC***********************-' WHERE setting_key = 'paypal_client_secret';

-- PayU Test Credentials
UPDATE site_settings SET setting_value = 'gtKFFx' WHERE setting_key = 'payu_merchant_key';
UPDATE site_settings SET setting_value = 'eCwWELxi' WHERE setting_key = 'payu_merchant_salt';

-- Enable test mode for all gateways
UPDATE site_settings SET setting_value = 'true' 
WHERE setting_key LIKE '%test_mode' AND setting_type = 'boolean';

-- Set development-friendly limits
UPDATE site_settings SET setting_value = '1000.00' WHERE setting_key = 'max_transaction_amount';
UPDATE site_settings SET setting_value = '10000.00' WHERE setting_key = 'daily_transaction_limit';

-- Enable all features for testing
UPDATE site_settings SET setting_value = 'true' WHERE setting_key IN (
    'auto_capture_payments',
    'allow_partial_refunds', 
    'enable_3d_secure',
    'send_payment_success_email',
    'enable_payment_analytics',
    'auto_generate_invoices',
    'enable_gateway_fallback'
);

SELECT 'Development payment configuration applied!' as status;
