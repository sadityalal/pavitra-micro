-- Default Site Settings for Pavitra Trading
INSERT INTO site_settings (setting_key, setting_value, setting_type) VALUES
-- Application Settings
('site_name', 'Pavitra Trading', 'string'),
('site_description', 'Your trusted online shopping destination in India', 'string'),
('app_debug', 'false', 'boolean'),
('maintenance_mode', 'false', 'boolean'),

-- Logging & Monitoring
('log_level', 'INFO', 'string'),

-- Security
('cors_origins', '["https://pavitra-trading.com", "https://www.pavitra-trading.com"]', 'json'),
('rate_limit_requests', '100', 'number'),
('rate_limit_window', '900', 'number'),

-- E-commerce Settings
('default_currency', 'INR', 'string'),
('currency_symbol', '₹', 'string'),
('supported_currencies', '["INR", "USD", "GBP", "EUR"]', 'json'),
('default_country', 'IN', 'string'),
('default_gst_rate', '18.00', 'number'),

-- Features
('enable_guest_checkout', 'true', 'boolean'),
('enable_reviews', 'true', 'boolean'),
('enable_wishlist', 'true', 'boolean'),

-- Order Settings
('min_order_amount', '0.00', 'number'),
('free_shipping_min_amount', '500.00', 'number'),

-- File Uploads
('max_upload_size', '5242880', 'number'),
('allowed_file_types', '["jpg", "jpeg", "png", "gif", "webp"]', 'json'),

-- Payment Settings
('razorpay_test_mode', 'false', 'boolean'),
('stripe_test_mode', 'false', 'boolean'),

-- Notification Settings
('email_notifications', 'true', 'boolean'),
('sms_notifications', 'true', 'boolean'),
('push_notifications', 'true', 'boolean')

ON DUPLICATE KEY UPDATE 
setting_value = VALUES(setting_value),
setting_type = VALUES(setting_type);

SELECT 'Site settings initialized successfully!' as status;
