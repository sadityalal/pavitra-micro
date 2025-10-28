-- Pavitra E-commerce Complete Database Migration Script
-- This script will recreate the entire database structure from scratch

SET FOREIGN_KEY_CHECKS = 0;

-- =============================================
-- 1. CORE USER TABLES
-- =============================================

-- Users table - Core user accounts
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) NOT NULL DEFAULT (uuid()),
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `first_name` varchar(100) NOT NULL,
  `last_name` varchar(100) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `country_code` varchar(5) DEFAULT '+91',
  `phone_verified` tinyint(1) DEFAULT '0',
  `avatar_url` varchar(500) DEFAULT NULL,
  `email_verified` tinyint(1) DEFAULT '0',
  `is_active` tinyint(1) DEFAULT '1',
  `is_admin` tinyint(1) DEFAULT '0',
  `last_login` timestamp NULL DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `gender` enum('male','female','other') DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_activity` datetime DEFAULT NULL,
  `dob_locked` tinyint(1) DEFAULT '0',
  `deactivated_at` datetime DEFAULT NULL,
  `deletion_requested_at` datetime DEFAULT NULL,
  `deletion_scheduled_at` datetime DEFAULT NULL,
  `dob_set` tinyint(1) NOT NULL DEFAULT '0',
  `dob_set_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_email` (`email`),
  KEY `idx_uuid` (`uuid`),
  KEY `idx_active` (`is_active`),
  KEY `idx_phone` (`phone`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Password history for security
DROP TABLE IF EXISTS `password_history`;
CREATE TABLE `password_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `password_history_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- User addresses
DROP TABLE IF EXISTS `user_addresses`;
CREATE TABLE `user_addresses` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `address_type` enum('shipping','billing') DEFAULT 'shipping',
  `full_name` varchar(200) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `country_code` varchar(5) DEFAULT '+91',
  `address_line1` varchar(255) NOT NULL,
  `address_line2` varchar(255) DEFAULT NULL,
  `landmark` varchar(255) DEFAULT NULL,
  `city` varchar(100) NOT NULL,
  `state` varchar(100) NOT NULL,
  `country` varchar(100) NOT NULL DEFAULT 'India',
  `postal_code` varchar(20) NOT NULL,
  `address_type_detail` enum('home','work','other') DEFAULT 'home',
  `is_default` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_address_type` (`address_type`),
  KEY `idx_country` (`country`),
  CONSTRAINT `user_addresses_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =============================================
-- 2. CATALOG MANAGEMENT TABLES
-- =============================================

-- Categories with hierarchy
DROP TABLE IF EXISTS `categories`;
CREATE TABLE `categories` (
  `id` int NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) NOT NULL DEFAULT (uuid()),
  `name` varchar(255) NOT NULL,
  `name_hindi` varchar(255) DEFAULT NULL,
  `slug` varchar(255) NOT NULL,
  `description` text,
  `description_hindi` text,
  `meta_title` varchar(255) DEFAULT NULL,
  `meta_description` text,
  `parent_id` int DEFAULT NULL,
  `image_url` varchar(500) DEFAULT NULL,
  `banner_url` varchar(500) DEFAULT NULL,
  `sort_order` int DEFAULT '0',
  `is_active` tinyint(1) DEFAULT '1',
  `is_featured` tinyint(1) DEFAULT '0',
  `gst_slab` decimal(5,2) DEFAULT '18.00',
  `hsn_code` varchar(10) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  UNIQUE KEY `slug` (`slug`),
  KEY `idx_slug` (`slug`),
  KEY `idx_parent` (`parent_id`),
  KEY `idx_active` (`is_active`),
  KEY `idx_featured` (`is_featured`),
  CONSTRAINT `categories_ibfk_1` FOREIGN KEY (`parent_id`) REFERENCES `categories` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Brands
DROP TABLE IF EXISTS `brands`;
CREATE TABLE `brands` (
  `id` int NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) NOT NULL DEFAULT (uuid()),
  `name` varchar(255) NOT NULL,
  `slug` varchar(255) NOT NULL,
  `description` text,
  `logo_url` varchar(500) DEFAULT NULL,
  `website_url` varchar(500) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `sort_order` int DEFAULT '0',
  `is_indian_brand` tinyint(1) DEFAULT '0',
  `brand_origin_country` varchar(100) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  UNIQUE KEY `slug` (`slug`),
  KEY `idx_slug` (`slug`),
  KEY `idx_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Products main table
DROP TABLE IF EXISTS `products`;
CREATE TABLE `products` (
  `id` int NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) NOT NULL DEFAULT (uuid()),
  `sku` varchar(100) NOT NULL,
  `name` varchar(255) NOT NULL,
  `slug` varchar(255) NOT NULL,
  `short_description` text,
  `description` longtext,
  `specification` json DEFAULT NULL,
  `base_price` decimal(12,2) NOT NULL,
  `compare_price` decimal(12,2) DEFAULT NULL,
  `cost_price` decimal(12,2) DEFAULT NULL,
  `gst_rate` decimal(5,2) DEFAULT '18.00',
  `hsn_code` varchar(10) DEFAULT NULL,
  `is_gst_inclusive` tinyint(1) DEFAULT '1',
  `track_inventory` tinyint(1) DEFAULT '1',
  `stock_quantity` int DEFAULT '0',
  `low_stock_threshold` int DEFAULT '5',
  `allow_backorders` tinyint(1) DEFAULT '0',
  `max_cart_quantity` int DEFAULT '10',
  `min_cart_quantity` int DEFAULT '1',
  `stock_status` enum('in_stock','low_stock','out_of_stock','on_backorder') DEFAULT 'out_of_stock',
  `product_type` enum('simple','variable','digital') DEFAULT 'simple',
  `is_virtual` tinyint(1) DEFAULT '0',
  `is_downloadable` tinyint(1) DEFAULT '0',
  `weight_grams` decimal(8,2) DEFAULT NULL,
  `length_cm` decimal(8,2) DEFAULT NULL,
  `width_cm` decimal(8,2) DEFAULT NULL,
  `height_cm` decimal(8,2) DEFAULT NULL,
  `main_image_url` varchar(500) DEFAULT NULL,
  `image_gallery` json DEFAULT NULL,
  `category_id` int NOT NULL,
  `brand_id` int DEFAULT NULL,
  `status` enum('draft','active','inactive','archived') DEFAULT 'draft',
  `is_featured` tinyint(1) DEFAULT '0',
  `is_trending` tinyint(1) DEFAULT '0',
  `is_bestseller` tinyint(1) DEFAULT '0',
  `is_on_sale` tinyint(1) DEFAULT '0',
  `is_returnable` tinyint(1) DEFAULT '1',
  `return_period_days` int DEFAULT '10',
  `warranty_period_months` int DEFAULT '0',
  `meta_title` varchar(255) DEFAULT NULL,
  `meta_description` text,
  `meta_keywords` text,
  `view_count` int DEFAULT '0',
  `wishlist_count` int DEFAULT '0',
  `total_sold` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  UNIQUE KEY `sku` (`sku`),
  UNIQUE KEY `slug` (`slug`),
  KEY `idx_slug` (`slug`),
  KEY `idx_sku` (`sku`),
  KEY `idx_category` (`category_id`),
  KEY `idx_brand` (`brand_id`),
  KEY `idx_status` (`status`),
  KEY `idx_featured` (`is_featured`),
  KEY `idx_stock_status` (`stock_status`),
  KEY `idx_on_sale` (`is_on_sale`),
  KEY `idx_trending` (`is_trending`),
  CONSTRAINT `products_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`),
  CONSTRAINT `products_ibfk_2` FOREIGN KEY (`brand_id`) REFERENCES `brands` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- =============================================
-- 3. PRODUCT ATTRIBUTES & VARIATIONS
-- =============================================

-- Product attributes (color, size, etc.)
DROP TABLE IF EXISTS `product_attributes`;
CREATE TABLE `product_attributes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `slug` varchar(100) NOT NULL,
  `type` enum('color','size','text','select') DEFAULT 'select',
  `is_visible` tinyint(1) DEFAULT '1',
  `sort_order` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `slug` (`slug`),
  KEY `idx_slug` (`slug`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Attribute values
DROP TABLE IF EXISTS `product_attribute_values`;
CREATE TABLE `product_attribute_values` (
  `id` int NOT NULL AUTO_INCREMENT,
  `attribute_id` int NOT NULL,
  `value` varchar(255) NOT NULL,
  `color_code` varchar(7) DEFAULT NULL,
  `image_url` varchar(500) DEFAULT NULL,
  `sort_order` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_attribute` (`attribute_id`),
  CONSTRAINT `product_attribute_values_ibfk_1` FOREIGN KEY (`attribute_id`) REFERENCES `product_attributes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Product variations
DROP TABLE IF EXISTS `product_variations`;
CREATE TABLE `product_variations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_id` int NOT NULL,
  `sku` varchar(100) NOT NULL,
  `price` decimal(12,2) DEFAULT NULL,
  `compare_price` decimal(12,2) DEFAULT NULL,
  `cost_price` decimal(12,2) DEFAULT NULL,
  `stock_quantity` int DEFAULT '0',
  `low_stock_threshold` int DEFAULT '5',
  `allow_backorders` tinyint(1) DEFAULT '0',
  `stock_status` enum('in_stock','low_stock','out_of_stock','on_backorder') DEFAULT 'out_of_stock',
  `weight_grams` decimal(8,2) DEFAULT NULL,
  `length_cm` decimal(8,2) DEFAULT NULL,
  `width_cm` decimal(8,2) DEFAULT NULL,
  `height_cm` decimal(8,2) DEFAULT NULL,
  `image_url` varchar(500) DEFAULT NULL,
  `is_default` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `sku` (`sku`),
  KEY `idx_product` (`product_id`),
  KEY `idx_sku` (`sku`),
  KEY `idx_stock_status` (`stock_status`),
  CONSTRAINT `product_variations_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Variation attributes linking
DROP TABLE IF EXISTS `variation_attributes`;
CREATE TABLE `variation_attributes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `variation_id` int NOT NULL,
  `attribute_id` int NOT NULL,
  `attribute_value_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_variation_attribute` (`variation_id`,`attribute_id`),
  KEY `attribute_id` (`attribute_id`),
  KEY `attribute_value_id` (`attribute_value_id`),
  KEY `idx_variation` (`variation_id`),
  CONSTRAINT `variation_attributes_ibfk_1` FOREIGN KEY (`variation_id`) REFERENCES `product_variations` (`id`) ON DELETE CASCADE,
  CONSTRAINT `variation_attributes_ibfk_2` FOREIGN KEY (`attribute_id`) REFERENCES `product_attributes` (`id`),
  CONSTRAINT `variation_attributes_ibfk_3` FOREIGN KEY (`attribute_value_id`) REFERENCES `product_attribute_values` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Product attribute association
DROP TABLE IF EXISTS `product_attribute_association`;
CREATE TABLE `product_attribute_association` (
  `product_id` int NOT NULL,
  `attribute_value_id` int NOT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`product_id`,`attribute_value_id`),
  KEY `attribute_value_id` (`attribute_value_id`),
  CONSTRAINT `product_attribute_association_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`),
  CONSTRAINT `product_attribute_association_ibfk_2` FOREIGN KEY (`attribute_value_id`) REFERENCES `product_attribute_values` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =============================================
-- 4. INVENTORY MANAGEMENT
-- =============================================

-- Stock movements audit
DROP TABLE IF EXISTS `stock_movements`;
CREATE TABLE `stock_movements` (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_id` int NOT NULL,
  `variation_id` int DEFAULT NULL,
  `movement_type` enum('purchase','sale','return','adjustment','damage','transfer_in','transfer_out') NOT NULL,
  `quantity` int NOT NULL,
  `stock_before` int NOT NULL,
  `stock_after` int NOT NULL,
  `reference_type` enum('order','purchase_order','adjustment','other') DEFAULT 'other',
  `reference_id` int DEFAULT NULL,
  `reason` text,
  `performed_by` int DEFAULT NULL,
  `performed_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `variation_id` (`variation_id`),
  KEY `performed_by` (`performed_by`),
  KEY `idx_product` (`product_id`),
  KEY `idx_movement_type` (`movement_type`),
  KEY `idx_performed_at` (`performed_at`),
  CONSTRAINT `stock_movements_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE,
  CONSTRAINT `stock_movements_ibfk_2` FOREIGN KEY (`variation_id`) REFERENCES `product_variations` (`id`) ON DELETE CASCADE,
  CONSTRAINT `stock_movements_ibfk_3` FOREIGN KEY (`performed_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Stock alerts
DROP TABLE IF EXISTS `stock_alerts`;
CREATE TABLE `stock_alerts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_id` int NOT NULL,
  `variation_id` int DEFAULT NULL,
  `alert_type` enum('low_stock','out_of_stock','over_stock') DEFAULT 'low_stock',
  `current_stock` int NOT NULL,
  `threshold` int NOT NULL,
  `is_resolved` tinyint(1) DEFAULT '0',
  `resolved_at` timestamp NULL DEFAULT NULL,
  `resolved_by` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `variation_id` (`variation_id`),
  KEY `resolved_by` (`resolved_by`),
  KEY `idx_product` (`product_id`),
  KEY `idx_resolved` (`is_resolved`),
  CONSTRAINT `stock_alerts_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE,
  CONSTRAINT `stock_alerts_ibfk_2` FOREIGN KEY (`variation_id`) REFERENCES `product_variations` (`id`) ON DELETE CASCADE,
  CONSTRAINT `stock_alerts_ibfk_3` FOREIGN KEY (`resolved_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =============================================
-- 5. SHOPPING & ORDERS
-- =============================================

-- Shopping cart
DROP TABLE IF EXISTS `shopping_cart`;
CREATE TABLE `shopping_cart` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `product_id` int NOT NULL,
  `variation_id` int DEFAULT NULL,
  `quantity` int NOT NULL DEFAULT '1',
  `cart_data` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_product_variation` (`user_id`,`product_id`,`variation_id`),
  KEY `product_id` (`product_id`),
  KEY `variation_id` (`variation_id`),
  KEY `idx_user` (`user_id`),
  CONSTRAINT `shopping_cart_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `shopping_cart_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE,
  CONSTRAINT `shopping_cart_ibfk_3` FOREIGN KEY (`variation_id`) REFERENCES `product_variations` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Wishlists
DROP TABLE IF EXISTS `wishlists`;
CREATE TABLE `wishlists` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `product_id` int NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_product` (`user_id`,`product_id`),
  KEY `product_id` (`product_id`),
  KEY `idx_user` (`user_id`),
  CONSTRAINT `wishlists_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `wishlists_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Orders main table
DROP TABLE IF EXISTS `orders`;
CREATE TABLE `orders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) NOT NULL DEFAULT (uuid()),
  `order_number` varchar(50) NOT NULL,
  `user_id` int NOT NULL,
  `subtotal` decimal(12,2) NOT NULL,
  `shipping_amount` decimal(12,2) DEFAULT '0.00',
  `tax_amount` decimal(12,2) DEFAULT '0.00',
  `discount_amount` decimal(12,2) DEFAULT '0.00',
  `total_amount` decimal(12,2) NOT NULL,
  `status` enum('pending','confirmed','processing','shipped','delivered','cancelled','refunded') DEFAULT 'pending',
  `payment_status` enum('pending','paid','failed','refunded','partially_refunded') DEFAULT 'pending',
  `payment_method` enum('credit_card','debit_card','upi','netbanking','cash_on_delivery','wallet') DEFAULT 'cash_on_delivery',
  `payment_gateway` varchar(100) DEFAULT NULL,
  `transaction_id` varchar(255) DEFAULT NULL,
  `upi_id` varchar(255) DEFAULT NULL,
  `shipping_method` varchar(100) DEFAULT NULL,
  `tracking_number` varchar(100) DEFAULT NULL,
  `shipping_address` json DEFAULT NULL,
  `billing_address` json DEFAULT NULL,
  `customer_note` text,
  `admin_note` text,
  `is_gst_invoice` tinyint(1) DEFAULT '1',
  `gst_number` varchar(15) DEFAULT NULL,
  `paid_at` timestamp NULL DEFAULT NULL,
  `shipped_at` timestamp NULL DEFAULT NULL,
  `delivered_at` timestamp NULL DEFAULT NULL,
  `cancelled_at` timestamp NULL DEFAULT NULL,
  `estimated_delivery` date DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  UNIQUE KEY `order_number` (`order_number`),
  KEY `idx_order_number` (`order_number`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_status` (`status`),
  KEY `idx_payment_status` (`payment_status`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Order items
DROP TABLE IF EXISTS `order_items`;
CREATE TABLE `order_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,
  `product_id` int NOT NULL,
  `variation_id` int DEFAULT NULL,
  `product_name` varchar(255) NOT NULL,
  `product_sku` varchar(100) NOT NULL,
  `product_image` varchar(500) DEFAULT NULL,
  `unit_price` decimal(12,2) NOT NULL,
  `quantity` int NOT NULL,
  `total_price` decimal(12,2) NOT NULL,
  `gst_rate` decimal(5,2) DEFAULT '18.00',
  `gst_amount` decimal(10,2) DEFAULT '0.00',
  `variation_attributes` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `variation_id` (`variation_id`),
  KEY `idx_order` (`order_id`),
  KEY `idx_product` (`product_id`),
  CONSTRAINT `order_items_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`) ON DELETE CASCADE,
  CONSTRAINT `order_items_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`),
  CONSTRAINT `order_items_ibfk_3` FOREIGN KEY (`variation_id`) REFERENCES `product_variations` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Order history audit
DROP TABLE IF EXISTS `order_history`;
CREATE TABLE `order_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,
  `field_changed` varchar(100) NOT NULL,
  `old_value` text,
  `new_value` text,
  `changed_by` int DEFAULT NULL,
  `change_type` enum('system','admin','customer') DEFAULT 'system',
  `reason` text,
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `changed_by` (`changed_by`),
  KEY `idx_order_id` (`order_id`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `order_history_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`) ON DELETE CASCADE,
  CONSTRAINT `order_history_ibfk_2` FOREIGN KEY (`changed_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =============================================
-- 6. PAYMENT SYSTEM
-- =============================================

-- Payment methods
DROP TABLE IF EXISTS `payment_methods`;
CREATE TABLE `payment_methods` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `method_type` enum('upi','card','netbanking','wallet','cash_on_delivery') NOT NULL,
  `is_default` tinyint(1) DEFAULT '0',
  `is_active` tinyint(1) DEFAULT '1',
  `upi_id` varchar(255) DEFAULT NULL,
  `upi_app` varchar(100) DEFAULT NULL,
  `card_last_four` varchar(4) DEFAULT NULL,
  `card_type` varchar(50) DEFAULT NULL,
  `card_network` varchar(100) DEFAULT NULL,
  `expiry_month` int DEFAULT NULL,
  `expiry_year` int DEFAULT NULL,
  `card_holder_name` varchar(255) DEFAULT NULL,
  `bank_name` varchar(255) DEFAULT NULL,
  `account_last_four` varchar(4) DEFAULT NULL,
  `wallet_provider` varchar(100) DEFAULT NULL,
  `wallet_id` varchar(255) DEFAULT NULL,
  `token` varchar(500) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_method_type` (`method_type`),
  KEY `idx_is_default` (`is_default`),
  CONSTRAINT `payment_methods_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Payment transactions
DROP TABLE IF EXISTS `payment_transactions`;
CREATE TABLE `payment_transactions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) NOT NULL DEFAULT (uuid()),
  `order_id` int NOT NULL,
  `user_id` int NOT NULL,
  `amount` decimal(12,2) NOT NULL,
  `currency` varchar(3) DEFAULT 'INR',
  `payment_method` varchar(50) NOT NULL,
  `gateway_name` varchar(100) DEFAULT NULL,
  `gateway_transaction_id` varchar(255) DEFAULT NULL,
  `gateway_order_id` varchar(255) DEFAULT NULL,
  `upi_id` varchar(255) DEFAULT NULL,
  `upi_transaction_id` varchar(255) DEFAULT NULL,
  `vpa` varchar(255) DEFAULT NULL,
  `card_last_four` varchar(4) DEFAULT NULL,
  `card_type` varchar(50) DEFAULT NULL,
  `card_network` varchar(100) DEFAULT NULL,
  `bank_name` varchar(255) DEFAULT NULL,
  `bank_transaction_id` varchar(255) DEFAULT NULL,
  `wallet_provider` varchar(100) DEFAULT NULL,
  `wallet_transaction_id` varchar(255) DEFAULT NULL,
  `status` enum('pending','processing','completed','failed','refunded') NOT NULL DEFAULT 'pending',
  `payment_status` enum('pending','authorized','captured','failed') NOT NULL DEFAULT 'pending',
  `failure_reason` text,
  `initiated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `authorized_at` timestamp NULL DEFAULT NULL,
  `captured_at` timestamp NULL DEFAULT NULL,
  `failed_at` timestamp NULL DEFAULT NULL,
  `refunded_at` timestamp NULL DEFAULT NULL,
  `refund_amount` decimal(12,2) DEFAULT '0.00',
  `refund_reason` text,
  `signature` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  KEY `idx_order_id` (`order_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_status` (`status`),
  KEY `idx_payment_method` (`payment_method`),
  CONSTRAINT `payment_transactions_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`) ON DELETE CASCADE,
  CONSTRAINT `payment_transactions_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =============================================
-- 7. MARKETING & PROMOTIONS
-- =============================================

-- Coupons
DROP TABLE IF EXISTS `coupons`;
CREATE TABLE `coupons` (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(50) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text,
  `discount_type` enum('percentage','fixed_amount','free_shipping') DEFAULT 'percentage',
  `discount_value` decimal(10,2) NOT NULL,
  `maximum_discount_amount` decimal(10,2) DEFAULT NULL,
  `minimum_order_amount` decimal(10,2) DEFAULT '0.00',
  `usage_limit` int DEFAULT NULL,
  `usage_limit_per_user` int DEFAULT NULL,
  `used_count` int DEFAULT '0',
  `valid_from` timestamp NULL DEFAULT NULL,
  `valid_until` timestamp NULL DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `apply_to` enum('all_products','specific_categories','specific_products') DEFAULT 'all_products',
  `applicable_categories` json DEFAULT NULL,
  `applicable_products` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `idx_code` (`code`),
  KEY `idx_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Coupon usage tracking
DROP TABLE IF EXISTS `coupon_usage`;
CREATE TABLE `coupon_usage` (
  `id` int NOT NULL AUTO_INCREMENT,
  `coupon_id` int NOT NULL,
  `user_id` int NOT NULL,
  `order_id` int NOT NULL,
  `discount_amount` decimal(10,2) NOT NULL,
  `used_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `order_id` (`order_id`),
  KEY `idx_coupon_user` (`coupon_id`,`user_id`),
  CONSTRAINT `coupon_usage_ibfk_1` FOREIGN KEY (`coupon_id`) REFERENCES `coupons` (`id`),
  CONSTRAINT `coupon_usage_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `coupon_usage_ibfk_3` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Banners
DROP TABLE IF EXISTS `banners`;
CREATE TABLE `banners` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `description` text,
  `image_url` varchar(500) NOT NULL,
  `target_url` varchar(500) DEFAULT NULL,
  `banner_type` enum('home_hero','home_slider','category_banner','sidebar_banner') DEFAULT 'home_slider',
  `sort_order` int DEFAULT '0',
  `is_active` tinyint(1) DEFAULT '1',
  `start_date` timestamp NULL DEFAULT NULL,
  `end_date` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_banner_type` (`banner_type`),
  KEY `idx_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =============================================
-- 8. REVIEWS & ENGAGEMENT
-- =============================================

-- Product reviews
DROP TABLE IF EXISTS `product_reviews`;
CREATE TABLE `product_reviews` (
  `id` int NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) NOT NULL DEFAULT (uuid()),
  `product_id` int NOT NULL,
  `user_id` int NOT NULL,
  `order_item_id` int DEFAULT NULL,
  `rating` tinyint NOT NULL,
  `title` varchar(255) DEFAULT NULL,
  `comment` text,
  `review_images` json DEFAULT NULL,
  `status` enum('pending','approved','rejected') DEFAULT 'pending',
  `is_verified_purchase` tinyint(1) DEFAULT '0',
  `helpful_count` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  UNIQUE KEY `unique_product_user` (`product_id`,`user_id`),
  KEY `user_id` (`user_id`),
  KEY `order_item_id` (`order_item_id`),
  KEY `idx_product` (`product_id`),
  KEY `idx_status` (`status`),
  KEY `idx_rating` (`rating`),
  CONSTRAINT `product_reviews_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE,
  CONSTRAINT `product_reviews_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `product_reviews_ibfk_3` FOREIGN KEY (`order_item_id`) REFERENCES `order_items` (`id`),
  CONSTRAINT `product_reviews_chk_1` CHECK (((`rating` >= 1) and (`rating` <= 5)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Review helpfulness
DROP TABLE IF EXISTS `review_helpfulness`;
CREATE TABLE `review_helpfulness` (
  `id` int NOT NULL AUTO_INCREMENT,
  `review_id` int NOT NULL,
  `user_id` int NOT NULL,
  `is_helpful` tinyint(1) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_review_user` (`review_id`,`user_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `review_helpfulness_ibfk_1` FOREIGN KEY (`review_id`) REFERENCES `product_reviews` (`id`) ON DELETE CASCADE,
  CONSTRAINT `review_helpfulness_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Product tags
DROP TABLE IF EXISTS `product_tags`;
CREATE TABLE `product_tags` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `slug` varchar(100) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `slug` (`slug`),
  KEY `idx_slug` (`slug`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Product tag relations
DROP TABLE IF EXISTS `product_tag_relations`;
CREATE TABLE `product_tag_relations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_id` int NOT NULL,
  `tag_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_product_tag` (`product_id`,`tag_id`),
  KEY `idx_product` (`product_id`),
  KEY `idx_tag` (`tag_id`),
  CONSTRAINT `product_tag_relations_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE,
  CONSTRAINT `product_tag_relations_ibfk_2` FOREIGN KEY (`tag_id`) REFERENCES `product_tags` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- =============================================
-- 9. REGIONAL & CONFIGURATION
-- =============================================

-- Indian states
DROP TABLE IF EXISTS `indian_states`;
CREATE TABLE `indian_states` (
  `id` int NOT NULL AUTO_INCREMENT,
  `state_name` varchar(100) NOT NULL,
  `state_code` varchar(10) NOT NULL,
  `is_union_territory` tinyint(1) DEFAULT '0',
  `is_active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`),
  KEY `idx_state_code` (`state_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Newsletter subscriptions
DROP TABLE IF EXISTS `newsletter_subscriptions`;
CREATE TABLE `newsletter_subscriptions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `subscribed_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Site settings
DROP TABLE IF EXISTS `site_settings`;
CREATE TABLE `site_settings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `setting_key` varchar(255) NOT NULL,
  `setting_value` text,
  `setting_type` enum('string','number','boolean','json') DEFAULT 'string',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `setting_key` (`setting_key`),
  KEY `idx_setting_key` (`setting_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- =============================================
-- 10. INSERT ESSENTIAL DATA
-- =============================================

-- Insert default Indian states
INSERT INTO `indian_states` (`state_name`, `state_code`, `is_union_territory`) VALUES
('Delhi', 'DL', 1),
('Maharashtra', 'MH', 0),
('Karnataka', 'KA', 0),
('Tamil Nadu', 'TN', 0),
('Uttar Pradesh', 'UP', 0),
('Gujarat', 'GJ', 0),
('Rajasthan', 'RJ', 0),
('West Bengal', 'WB', 0);

-- Insert default site settings
INSERT INTO `site_settings` (`setting_key`, `setting_value`, `setting_type`) VALUES
('site_name', 'Pavitra Trading', 'string'),
('site_description', 'Your trusted online shopping destination', 'string'),
('currency', 'INR', 'string'),
('currency_symbol', '₹', 'string'),
('default_gst_rate', '18.00', 'number'),
('enable_guest_checkout', '1', 'boolean'),
('maintenance_mode', '0', 'boolean'),
('enable_reviews', '1', 'boolean'),
('enable_wishlist', '1', 'boolean'),
('min_order_amount', '0.00', 'number'),
('free_shipping_min_amount', '500.00', 'number');

-- Insert default product attributes
INSERT INTO `product_attributes` (`name`, `slug`, `type`, `sort_order`) VALUES
('Color', 'color', 'color', 1),
('Size', 'size', 'select', 2),
('Storage', 'storage', 'select', 3),
('RAM', 'ram', 'select', 4);

-- Insert default attribute values
INSERT INTO `product_attribute_values` (`attribute_id`, `value`, `color_code`, `sort_order`) VALUES
(1, 'Black', '#000000', 1),
(1, 'White', '#FFFFFF', 2),
(1, 'Red', '#FF0000', 3),
(1, 'Blue', '#0000FF', 4),
(2, 'S', NULL, 1),
(2, 'M', NULL, 2),
(2, 'L', NULL, 3),
(2, 'XL', NULL, 4),
(3, '64GB', NULL, 1),
(3, '128GB', NULL, 2),
(3, '256GB', NULL, 3),
(4, '4GB', NULL, 1),
(4, '6GB', NULL, 2),
(4, '8GB', NULL, 3);

-- Create default admin user (password: admin123)
INSERT INTO `users` (`email`, `password_hash`, `first_name`, `last_name`, `is_admin`, `email_verified`) VALUES
('admin@pavitra.com', '$2b$12$LQv3c1yqBWVHxkd0L8k7Oe7F3l2M3a7N8Yb7nB5c3d5f7g9h2j4k6', 'Admin', 'User', 1, 1);

-- 1. Add new tables for enhanced functionality

-- Countries table for international support
CREATE TABLE IF NOT EXISTS `countries` (
  `id` int NOT NULL AUTO_INCREMENT,
  `country_name` varchar(100) NOT NULL,
  `country_code` varchar(2) NOT NULL,
  `country_code_3` varchar(3) NOT NULL,
  `phone_code` varchar(5) NOT NULL,
  `currency_code` varchar(3) NOT NULL,
  `currency_symbol` varchar(10) NOT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `tax_type` enum('gst','vat','sales_tax') DEFAULT 'gst',
  `default_tax_rate` decimal(5,2) DEFAULT '0.00',
  `sort_order` int DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `country_code` (`country_code`),
  UNIQUE KEY `country_code_3` (`country_code_3`),
  KEY `idx_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Banks table for netbanking
CREATE TABLE IF NOT EXISTS `banks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) NOT NULL DEFAULT (uuid()),
  `bank_name` varchar(255) NOT NULL,
  `bank_code` varchar(50) NOT NULL,
  `logo_url` varchar(500) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `supported_payment_types` json DEFAULT NULL,
  `sort_order` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  UNIQUE KEY `bank_code` (`bank_code`),
  KEY `idx_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- File storage for local images
CREATE TABLE IF NOT EXISTS `file_storage` (
  `id` int NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) NOT NULL DEFAULT (uuid()),
  `file_name` varchar(255) NOT NULL,
  `file_path` varchar(500) NOT NULL,
  `file_size` int DEFAULT '0',
  `mime_type` varchar(100) NOT NULL,
  `file_type` enum('user_avatar','product_image','category_image','brand_logo','bank_logo') NOT NULL,
  `entity_type` varchar(50) DEFAULT NULL,
  `entity_id` int DEFAULT NULL,
  `uploaded_by` int DEFAULT NULL,
  `is_public` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  UNIQUE KEY `file_path` (`file_path`),
  KEY `idx_file_type` (`file_type`),
  KEY `idx_entity` (`entity_type`,`entity_id`),
  KEY `idx_uploaded_by` (`uploaded_by`),
  CONSTRAINT `file_storage_ibfk_1` FOREIGN KEY (`uploaded_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Payment gateways configuration
CREATE TABLE IF NOT EXISTS `payment_gateways` (
  `id` int NOT NULL AUTO_INCREMENT,
  `gateway_name` varchar(100) NOT NULL,
  `gateway_code` varchar(50) NOT NULL,
  `is_active` tinyint(1) DEFAULT '0',
  `is_live` tinyint(1) DEFAULT '0',
  `supported_countries` json DEFAULT NULL,
  `supported_currencies` json DEFAULT NULL,
  `config` json DEFAULT NULL,
  `sort_order` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `gateway_code` (`gateway_code`),
  KEY `idx_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- User tax information for GST/VAT
CREATE TABLE IF NOT EXISTS `user_tax_info` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `country_id` int NOT NULL,
  `tax_number` varchar(50) DEFAULT NULL,
  `tax_type` enum('gst','vat','pan') DEFAULT NULL,
  `business_name` varchar(255) DEFAULT NULL,
  `business_address` text,
  `is_verified` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_country` (`user_id`,`country_id`),
  KEY `idx_country` (`country_id`),
  KEY `idx_tax_number` (`tax_number`),
  CONSTRAINT `user_tax_info_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `user_tax_info_ibfk_2` FOREIGN KEY (`country_id`) REFERENCES `countries` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 2. Modify existing tables

-- Add columns to users table
ALTER TABLE `users`
ADD COLUMN `country_id` int DEFAULT NULL AFTER `phone`,
ADD COLUMN `username` varchar(100) DEFAULT NULL AFTER `email`,
ADD COLUMN `avatar_file_id` int DEFAULT NULL AFTER `avatar_url`,
ADD COLUMN `preferred_currency` varchar(3) DEFAULT 'INR' AFTER `country_id`,
ADD COLUMN `preferred_language` varchar(10) DEFAULT 'en' AFTER `preferred_currency`,
ADD UNIQUE KEY `username` (`username`),
ADD KEY `idx_country` (`country_id`),
ADD KEY `idx_avatar_file` (`avatar_file_id`);

-- Add foreign key constraints for users table
ALTER TABLE `users`
ADD CONSTRAINT `users_ibfk_country` FOREIGN KEY (`country_id`) REFERENCES `countries` (`id`),
ADD CONSTRAINT `users_ibfk_avatar` FOREIGN KEY (`avatar_file_id`) REFERENCES `file_storage` (`id`);

-- Add columns to products table for international pricing
ALTER TABLE `products`
ADD COLUMN `base_currency` varchar(3) DEFAULT 'INR' AFTER `base_price`,
ADD COLUMN `international_pricing` json DEFAULT NULL AFTER `base_currency`;

-- 3. Insert initial data

-- Insert countries
INSERT INTO `countries` (`country_name`, `country_code`, `country_code_3`, `phone_code`, `currency_code`, `currency_symbol`, `tax_type`, `default_tax_rate`) VALUES
('India', 'IN', 'IND', '+91', 'INR', '₹', 'gst', 18.00),
('United States', 'US', 'USA', '+1', 'USD', '$', 'sales_tax', 7.50),
('United Kingdom', 'GB', 'GBR', '+44', 'GBP', '£', 'vat', 20.00),
('Germany', 'DE', 'DEU', '+49', 'EUR', '€', 'vat', 19.00),
('Australia', 'AU', 'AUS', '+61', 'AUD', 'A$', 'gst', 10.00);

-- Insert banks
INSERT INTO `banks` (`bank_name`, `bank_code`, `supported_payment_types`) VALUES
('State Bank of India', 'SBI', '["netbanking", "debit_card", "upi"]'),
('HDFC Bank', 'HDFC', '["netbanking", "credit_card", "debit_card", "upi"]'),
('ICICI Bank', 'ICICI', '["netbanking", "credit_card", "debit_card", "upi"]'),
('Axis Bank', 'AXIS', '["netbanking", "credit_card", "debit_card", "upi"]'),
('Punjab National Bank', 'PNB', '["netbanking", "debit_card", "upi"]');

-- Insert payment gateways
INSERT INTO `payment_gateways` (`gateway_name`, `gateway_code`, `is_active`, `supported_countries`, `supported_currencies`, `config`) VALUES
('Razorpay', 'razorpay', 1, '["IN"]', '["INR"]', '{"test_mode": true, "test_key": "rzp_test_...", "test_secret": "..."}'),
('Stripe', 'stripe', 1, '["US", "GB", "DE", "AU", "IN"]', '["USD", "GBP", "EUR", "AUD", "INR"]', '{"test_mode": true, "test_key": "pk_test_...", "test_secret": "..."}'),
('PayPal', 'paypal', 1, '["US", "GB", "DE", "AU"]', '["USD", "GBP", "EUR", "AUD"]', '{"test_mode": true, "client_id": "...", "client_secret": "..."}');

-- 4. Update existing data

-- Set default country for existing users
UPDATE `users` SET `country_id` = (SELECT id FROM countries WHERE country_code = 'IN') WHERE country_id IS NULL;

-- Add username for existing admin user
UPDATE `users` SET `username` = 'admin' WHERE email = 'admin@pavitra.com' AND username IS NULL;

-- Update site settings for multi-currency
INSERT INTO `site_settings` (`setting_key`, `setting_value`, `setting_type`) VALUES
('default_currency', 'INR', 'string'),
('supported_currencies', '["INR", "USD", "GBP", "EUR", "AUD"]', 'json'),
('default_country', 'IN', 'string'),
('file_upload_path', '/app/uploads', 'string'),
('max_upload_size', '5242880', 'number'),
('allowed_file_types', '["jpg", "jpeg", "png", "gif", "webp"]', 'json');

SELECT 'Database enhancements completed successfully!' as status;

-- =============================================
-- 11. Normal SEttings Frontend
-- =============================================
-- Site settings
DROP TABLE IF EXISTS `frontend_settings`;
CREATE TABLE `frontend_settings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `setting_key` varchar(255) NOT NULL,
  `setting_value` text,
  `setting_type` enum('string','number','boolean','json') DEFAULT 'string',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `setting_key` (`setting_key`),
  KEY `idx_setting_key` (`setting_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

SET FOREIGN_KEY_CHECKS = 1;


-- =============================================
-- FINAL MESSAGE
-- =============================================

SELECT 'Database migration completed successfully!' as status;


