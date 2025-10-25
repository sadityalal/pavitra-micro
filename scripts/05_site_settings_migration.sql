UPDATE site_settings SET
    setting_value = 'redis',
    updated_at = NOW()
WHERE setting_key = 'redis_host';

UPDATE site_settings SET
    setting_value = 'rabbitmq',
    updated_at = NOW()
WHERE setting_key = 'rabbitmq_host';

UPDATE site_settings SET
    setting_value = 'admin',
    updated_at = NOW()
WHERE setting_key = 'rabbitmq_user';

UPDATE site_settings SET
    setting_value = 'admin123',
    updated_at = NOW()
WHERE setting_key = 'rabbitmq_password';

-- scripts/06_missing_settings.sql
INSERT INTO site_settings (setting_key, setting_value, setting_type) VALUES
('free_shipping_threshold', '999', 'number'),
('return_period_days', '10', 'number'),
('site_phone', '+91-9711317009', 'string'),
('site_email', 'support@pavitraenterprises.com', 'string'),
('business_hours', '{"monday_friday": "9am-6pm", "saturday": "10am-4pm", "sunday": "Closed"}', 'json'),
('gst_number', '', 'string'),
('email_from_name', 'Pavitra Trading', 'string')
ON DUPLICATE KEY UPDATE
setting_value = VALUES(setting_value),
setting_type = VALUES(setting_type);