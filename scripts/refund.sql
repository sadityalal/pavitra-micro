-- Refunds table for handling payment refunds
CREATE TABLE IF NOT EXISTS `refunds` (
  `id` int NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) NOT NULL DEFAULT (uuid()),
  `payment_id` int NOT NULL,
  `order_id` int NOT NULL,
  `amount` decimal(12,2) NOT NULL,
  `currency` varchar(3) DEFAULT 'INR',
  `reason` text,
  `status` enum('pending','processing','completed','failed') DEFAULT 'pending',
  `gateway_refund_id` varchar(255) DEFAULT NULL,
  `failure_reason` text,
  `processed_by` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `processed_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `idx_payment_id` (`payment_id`),
  KEY `idx_order_id` (`order_id`),
  KEY `idx_status` (`status`),
  KEY `idx_processed_by` (`processed_by`),
  CONSTRAINT `refunds_ibfk_1` FOREIGN KEY (`payment_id`) REFERENCES `payment_transactions` (`id`),
  CONSTRAINT `refunds_ibfk_2` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`),
  CONSTRAINT `refunds_ibfk_3` FOREIGN KEY (`processed_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Update payment_transactions table to track refunds better
ALTER TABLE `payment_transactions`
ADD COLUMN `total_refunded` decimal(12,2) DEFAULT '0.00' AFTER `refund_amount`;

-- Add refund settings to site_settings
INSERT INTO site_settings (setting_key, setting_value, setting_type) VALUES
('refund_policy_days', '30', 'number'),
('auto_refund_enabled', 'true', 'boolean'),
('refund_processing_fee', '0.00', 'number')
ON DUPLICATE KEY UPDATE
setting_value = VALUES(setting_value),
setting_type = VALUES(setting_type);

SELECT 'Refunds table and settings created successfully!' as status;