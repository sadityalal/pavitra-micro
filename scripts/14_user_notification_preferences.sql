-- Create user notification preferences table
CREATE TABLE IF NOT EXISTS user_notification_preferences (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    notification_method ENUM('email', 'telegram', 'whatsapp', 'sms', 'push') NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY unique_user_method (user_id, notification_method),
    KEY idx_user_id (user_id),
    KEY idx_method (notification_method),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Add default notification preferences for existing users (email only)
INSERT INTO user_notification_preferences (user_id, notification_method, is_enabled)
SELECT 
    id as user_id, 
    'email' as notification_method, 
    TRUE as is_enabled
FROM users
ON DUPLICATE KEY UPDATE is_enabled = VALUES(is_enabled);

-- Add Telegram and WhatsApp fields to users table
ALTER TABLE users 
ADD COLUMN telegram_username VARCHAR(100) NULL AFTER phone,
ADD COLUMN telegram_phone VARCHAR(20) NULL AFTER telegram_username,
ADD COLUMN whatsapp_phone VARCHAR(20) NULL AFTER telegram_phone;

-- Add indexes
CREATE INDEX idx_user_telegram_username ON users(telegram_username);
CREATE INDEX idx_user_telegram_phone ON users(telegram_phone);
CREATE INDEX idx_user_whatsapp_phone ON users(whatsapp_phone);

SELECT 'User notification preferences system created successfully!' as status;
