INSERT INTO site_settings (setting_key, setting_value, setting_type) VALUES
('telegram_notifications', 'false', 'boolean'),
('telegram_bot_token', '', 'string'),
('telegram_chat_id', '', 'string'),
('whatsapp_notifications', 'false', 'boolean'),
('whatsapp_api_url', '', 'string'),
('whatsapp_api_token', '', 'string'),
('email_from_name', 'Pavitra Trading', 'string'),
('sms_notifications', 'false', 'boolean'),
('push_notifications', 'false', 'boolean')
ON DUPLICATE KEY UPDATE
setting_value = VALUES(setting_value),
setting_type = VALUES(setting_type);

ALTER TABLE notification_logs
MODIFY COLUMN type ENUM('email','sms','push','telegram','whatsapp') NOT NULL;

SELECT 'Notification settings added successfully!' as status;
