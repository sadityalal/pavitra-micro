-- Quick development setup for payment gateways
-- Use test credentials for development

UPDATE site_settings SET 
setting_value = 'rzp_test_xxxxxxxxxxxx',
setting_type = 'string'
WHERE setting_key = 'razorpay_key_id';

UPDATE site_settings SET 
setting_value = 'razorpay_test_secret_xxxxxxxx',
setting_type = 'string' 
WHERE setting_key = 'razorpay_secret';

UPDATE site_settings SET 
setting_value = 'sk_test_xxxxxxxxxxxxxxxxxxxx',
setting_type = 'string'
WHERE setting_key = 'stripe_secret_key';

UPDATE site_settings SET 
setting_value = 'pk_test_xxxxxxxxxxxxxxxxxxxx',
setting_type = 'string'
WHERE setting_key = 'stripe_publishable_key';

-- Enable test mode
UPDATE site_settings SET 
setting_value = 'true',
setting_type = 'boolean'
WHERE setting_key IN ('razorpay_test_mode', 'stripe_test_mode');

SELECT 'Payment development setup completed!' as status;

-- Show current payment settings
SELECT setting_key, 
       CASE 
           WHEN setting_key LIKE '%secret%' OR setting_key LIKE '%key%' THEN 
               CASE 
                   WHEN LENGTH(setting_value) > 8 THEN CONCAT(SUBSTRING(setting_value, 1, 8), '...')
                   ELSE 'NOT_SET'
               END
           ELSE setting_value 
       END as setting_value,
       setting_type
FROM site_settings 
WHERE setting_key LIKE '%razorpay%' OR setting_key LIKE '%stripe%' OR setting_key LIKE '%payment%';
