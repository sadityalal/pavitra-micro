-- Complete Payment Gateway Configuration for Site Settings
-- Includes all supported gateways with proper defaults

-- Razorpay Settings (Primary - India Focused)
INSERT INTO site_settings (setting_key, setting_value, setting_type) VALUES
('razorpay_key_id', 'rzp_test_YOUR_RAZORPAY_KEY', 'string'),
('razorpay_secret', 'YOUR_RAZORPAY_SECRET', 'string'),
('razorpay_test_mode', 'true', 'boolean'),
('razorpay_webhook_secret', 'YOUR_RAZORPAY_WEBHOOK_SECRET', 'string'),
('razorpay_max_amount', '10000000', 'number'), -- 10 Lakh in paise
('razorpay_min_amount', '100', 'number'), -- 1 Rupee in paise

-- Stripe Settings (Global Cards)
('stripe_secret_key', 'sk_test_YOUR_STRIPE_SECRET', 'string'),
('stripe_publishable_key', 'pk_test_YOUR_STRIPE_PUBLISHABLE', 'string'),
('stripe_test_mode', 'true', 'boolean'),
('stripe_webhook_secret', 'whsec_YOUR_STRIPE_WEBHOOK', 'string'),
('stripe_currency', 'inr', 'string'),

-- PayPal Settings (Global - Redirect Based)
('paypal_client_id', 'YOUR_PAYPAL_CLIENT_ID', 'string'),
('paypal_client_secret', 'YOUR_PAYPAL_CLIENT_SECRET', 'string'),
('paypal_test_mode', 'true', 'boolean'),
('paypal_webhook_id', 'YOUR_PAYPAL_WEBHOOK_ID', 'string'),
('paypal_currency', 'USD', 'string'),

-- PayU Settings (India Alternative)
('payu_merchant_key', 'YOUR_PAYU_MERCHANT_KEY', 'string'),
('payu_merchant_salt', 'YOUR_PAYU_MERCHANT_SALT', 'string'),
('payu_test_mode', 'true', 'boolean'),
('payu_authorization_header', 'YOUR_PAYU_AUTH_HEADER', 'string'),

-- CCAvenue Settings (India - Enterprise)
('ccavenue_merchant_id', 'YOUR_CCAVENUE_MERCHANT_ID', 'string'),
('ccavenue_access_code', 'YOUR_CCAVENUE_ACCESS_CODE', 'string'),
('ccavenue_working_key', 'YOUR_CCAVENUE_WORKING_KEY', 'string'),
('ccavenue_test_mode', 'true', 'boolean'),

-- Instamojo Settings (India - P2P)
('instamojo_client_id', 'YOUR_INSTAMOJO_CLIENT_ID', 'string'),
('instamojo_client_secret', 'YOUR_INSTAMOJO_CLIENT_SECRET', 'string'),
('instamojo_test_mode', 'true', 'boolean'),
('instamojo_auth_token', 'YOUR_INSTAMOJO_AUTH_TOKEN', 'string'),

-- Payment Configuration
('payment_timeout_minutes', '30', 'number'),
('max_payment_attempts', '3', 'number'),
('auto_capture_payments', 'true', 'boolean'),
('allow_partial_refunds', 'true', 'boolean'),
('refund_processing_days', '7', 'number'),
('payment_verification_timeout', '900', 'number'), -- 15 minutes

-- Security & Limits
('require_cvv_for_saved_cards', 'true', 'boolean'),
('token_expiry_minutes', '5', 'number'),
('max_saved_cards_per_user', '5', 'number'),
('enable_3d_secure', 'true', 'boolean'),
('enable_risk_analysis', 'true', 'boolean'),

-- Transaction Limits
('min_transaction_amount', '1.00', 'number'),
('max_transaction_amount', '100000.00', 'number'),
('daily_transaction_limit', '500000.00', 'number'),
('weekly_transaction_limit', '2000000.00', 'number'),

-- Fees & Charges
('transaction_fee_percent', '2.5', 'number'),
('transaction_fee_fixed', '2.00', 'number'),
('gst_on_fees', '18.0', 'number'),
('international_fee_surcharge', '3.5', 'number'),

-- Supported Methods & Gateways
('supported_payment_methods', '["credit_card", "debit_card", "upi", "netbanking", "cash_on_delivery", "wallet"]', 'json'),
('supported_gateways', '["razorpay", "stripe", "paypal", "payu", "ccavenue", "instamojo", "cash_on_delivery"]', 'json'),
('default_payment_gateway', 'razorpay', 'string'),

-- UPI Configuration
('supported_upi_apps', '["google_pay", "phonepe", "paytm", "bhim_upi", "amazon_pay"]', 'json'),
('upi_collect_timeout', '300', 'number'),
('upi_max_amount', '100000', 'number'),

-- Netbanking Configuration
('supported_banks', '["sbi", "hdfc", "icici", "axis", "kotak", "indusind", "yesbank"]', 'json'),
('netbanking_timeout', '900', 'number'),

-- Wallet Configuration
('supported_wallets', '["paytm", "phonepe", "mobikwik", "freecharge", "amazon_pay", "olamoney"]', 'json'),
('wallet_max_amount', '20000', 'number'),

-- Cash on Delivery Configuration
('cod_max_amount', '50000', 'number'),
('cod_available_pincodes', '["*"]', 'json'), -- * means all pincodes
('cod_advance_percent', '0', 'number'),

-- Currency Settings
('base_currency', 'INR', 'string'),
('supported_currencies', '["INR", "USD", "EUR", "GBP", "AED", "SGD"]', 'json'),
('currency_conversion_enabled', 'false', 'boolean'),

-- Webhook URLs (for reference)
('razorpay_webhook_url', 'https://yourdomain.com/api/v1/payments/webhook/razorpay', 'string'),
('stripe_webhook_url', 'https://yourdomain.com/api/v1/payments/webhook/stripe', 'string'),
('paypal_webhook_url', 'https://yourdomain.com/api/v1/payments/webhook/paypal', 'string'),
('payu_webhook_url', 'https://yourdomain.com/api/v1/payments/webhook/payu', 'string'),

-- Notification Settings
('send_payment_success_email', 'true', 'boolean'),
('send_payment_failure_email', 'true', 'boolean'),
('send_refund_processed_email', 'true', 'boolean'),
('payment_success_sms', 'true', 'boolean'),

-- Analytics & Reporting
('enable_payment_analytics', 'true', 'boolean'),
('payment_retention_days', '1095', 'number'), -- 3 years
('auto_generate_invoices', 'true', 'boolean'),

-- Fallback & Redundancy
('primary_gateway', 'razorpay', 'string'),
('secondary_gateway', 'stripe', 'string'),
('enable_gateway_fallback', 'true', 'boolean'),
('gateway_failure_threshold', '5', 'number')

ON DUPLICATE KEY UPDATE
setting_value = VALUES(setting_value),
setting_type = VALUES(setting_type);

-- Verify the settings were added
SELECT 'Complete payment gateway settings added successfully!' as status;

-- Show all payment-related settings
SELECT 
    setting_key, 
    CASE 
        WHEN setting_key LIKE '%secret%' OR setting_key LIKE '%key%' OR setting_key LIKE '%token%' THEN
            CASE 
                WHEN LENGTH(setting_value) > 8 THEN CONCAT(SUBSTRING(setting_value, 1, 8), '...')
                ELSE 'NOT_SET'
            END
        ELSE setting_value 
    END as setting_value,
    setting_type
FROM site_settings 
WHERE setting_key LIKE '%payment%' 
   OR setting_key LIKE '%razorpay%' 
   OR setting_key LIKE '%stripe%'
   OR setting_key LIKE '%paypal%'
   OR setting_key LIKE '%payu%'
   OR setting_key LIKE '%ccavenue%'
   OR setting_key LIKE '%instamojo%'
   OR setting_key LIKE '%transaction%'
   OR setting_key LIKE '%refund%'
   OR setting_key LIKE '%gateway%'
   OR setting_key LIKE '%upi%'
   OR setting_key LIKE '%netbanking%'
   OR setting_key LIKE '%wallet%'
   OR setting_key LIKE '%cod%'
ORDER BY setting_key;
