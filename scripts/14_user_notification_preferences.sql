-- Create user notification preferences table
CREATE TABLE IF NOT EXISTS user_notification_preferences (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    notification_method ENUM('email', 'sms', 'telegram', 'whatsapp', 'push') NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    priority_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY unique_user_method (user_id, notification_method),
    KEY idx_user_id (user_id),
    KEY idx_method (notification_method),
    KEY idx_enabled (is_enabled),
    CONSTRAINT fk_user_notif_prefs_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Add default notification preferences for all existing users
INSERT INTO user_notification_preferences (user_id, notification_method, is_enabled, priority_order)
SELECT 
    id as user_id, 
    'email' as notification_method, 
    TRUE as is_enabled, 
    1 as priority_order
FROM users
ON DUPLICATE KEY UPDATE is_enabled = VALUES(is_enabled);

-- Add Telegram fields to users table (for username/phone storage)
ALTER TABLE users 
ADD COLUMN telegram_username VARCHAR(100) NULL AFTER phone,
ADD COLUMN telegram_phone VARCHAR(20) NULL AFTER telegram_username;

-- Add indexes
CREATE INDEX idx_user_telegram_username ON users(telegram_username);
CREATE INDEX idx_user_telegram_phone ON users(telegram_phone);

SELECT 'User notification preferences system created successfully!' as status;
