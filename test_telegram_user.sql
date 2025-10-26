-- Update the admin user with Telegram credentials
UPDATE users 
SET telegram_username = 'saurabh_aditya'
WHERE email = 'admin@pavitra.com';

-- Enable Telegram notifications for admin user
UPDATE user_notification_preferences 
SET is_enabled = TRUE 
WHERE user_id = (SELECT id FROM users WHERE email = 'admin@pavitra.com') 
AND notification_method = 'telegram';

-- Verify the update
SELECT 
    u.id, u.email, u.telegram_username, u.telegram_phone,
    unp.notification_method, unp.is_enabled, unp.priority_order
FROM users u
JOIN user_notification_preferences unp ON u.id = unp.user_id
WHERE u.email = 'admin@pavitra.com';
