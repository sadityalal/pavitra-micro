-- Create notification logs table if it doesn't exist
CREATE TABLE IF NOT EXISTS `notification_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type` enum('email','sms','push') NOT NULL,
  `recipient` varchar(255) NOT NULL,
  `subject` varchar(500) DEFAULT NULL,
  `message` text,
  `status` enum('sent','failed','pending') DEFAULT 'sent',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_type` (`type`),
  KEY `idx_recipient` (`recipient`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

SELECT 'Notification logs table created successfully!' as status;
