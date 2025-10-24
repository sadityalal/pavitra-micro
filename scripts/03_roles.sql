-- Add user roles and permissions system
SET FOREIGN_KEY_CHECKS = 0;

-- User Roles Table
CREATE TABLE IF NOT EXISTS `user_roles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` text,
  `is_system_role` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Permissions Table
CREATE TABLE IF NOT EXISTS `permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` text,
  `module` varchar(50) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Role Permissions (Many-to-Many)
CREATE TABLE IF NOT EXISTS `role_permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `role_id` int NOT NULL,
  `permission_id` int NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_role_permission` (`role_id`,`permission_id`),
  KEY `permission_id` (`permission_id`),
  CONSTRAINT `role_permissions_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `user_roles` (`id`) ON DELETE CASCADE,
  CONSTRAINT `role_permissions_ibfk_2` FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- User Roles Assignment (Connects users to roles)
CREATE TABLE IF NOT EXISTS `user_role_assignments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `role_id` int NOT NULL,
  `assigned_by` int DEFAULT NULL,
  `assigned_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_role` (`user_id`,`role_id`),
  KEY `role_id` (`role_id`),
  KEY `assigned_by` (`assigned_by`),
  CONSTRAINT `user_role_assignments_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `user_role_assignments_ibfk_2` FOREIGN KEY (`role_id`) REFERENCES `user_roles` (`id`) ON DELETE CASCADE,
  CONSTRAINT `user_role_assignments_ibfk_3` FOREIGN KEY (`assigned_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Insert System Roles
INSERT INTO `user_roles` (`name`, `description`, `is_system_role`) VALUES
('super_admin', 'Full system access including site settings and user management', 1),
('admin', 'Administrative access for product management, orders, and user support', 1),
('customer', 'Regular customer with shopping privileges', 1),
('vendor', 'Vendor who can manage their own products', 1),
('content_manager', 'Can manage content, categories, and banners', 1),
('support_staff', 'Can manage customer support and orders', 1);

-- Insert Permissions
INSERT INTO `permissions` (`name`, `description`, `module`) VALUES
-- Site Management Permissions
('manage_site_settings', 'Can update site settings, logos, themes', 'site'),
('manage_logs', 'Can view and manage system logs', 'site'),
('manage_backups', 'Can create and restore backups', 'site'),

-- User Management Permissions
('view_users', 'Can view user list and profiles', 'users'),
('manage_users', 'Can create, edit, and delete users', 'users'),
('assign_roles', 'Can assign roles to users', 'users'),
('manage_user_roles', 'Can create and manage user roles', 'users'),

-- Product Management Permissions
('view_products', 'Can view all products', 'products'),
('manage_products', 'Can create, edit, and delete products', 'products'),
('manage_categories', 'Can manage product categories', 'products'),
('manage_brands', 'Can manage brands', 'products'),
('manage_inventory', 'Can update stock levels', 'products'),
('view_analytics', 'Can view product analytics', 'products'),

-- Order Management Permissions
('view_orders', 'Can view all orders', 'orders'),
('manage_orders', 'Can update order status and details', 'orders'),
('process_refunds', 'Can process refunds and cancellations', 'orders'),
('view_sales_reports', 'Can view sales reports', 'orders'),

-- Content Management Permissions
('manage_banners', 'Can manage homepage banners', 'content'),
('manage_pages', 'Can manage static pages', 'content'),
('manage_reviews', 'Can moderate product reviews', 'content'),
('manage_blog', 'Can manage blog posts', 'content'),

-- Payment & Financial Permissions
('view_payments', 'Can view payment transactions', 'payments'),
('manage_payment_gateways', 'Can configure payment methods', 'payments'),
('view_financial_reports', 'Can view financial reports', 'payments'),

-- Customer Support Permissions
('manage_tickets', 'Can manage support tickets', 'support'),
('view_customer_data', 'Can view customer information', 'support'),
('send_notifications', 'Can send notifications to users', 'support');

-- Assign Permissions to Super Admin (All permissions)
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
SELECT 
    (SELECT id FROM user_roles WHERE name = 'super_admin'),
    id 
FROM permissions;

-- Assign Permissions to Admin (Most administrative permissions)
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
SELECT 
    (SELECT id FROM user_roles WHERE name = 'admin'),
    id 
FROM permissions 
WHERE name NOT IN ('manage_site_settings', 'manage_user_roles', 'manage_backups');

-- Assign Permissions to Content Manager
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
SELECT 
    (SELECT id FROM user_roles WHERE name = 'content_manager'),
    id 
FROM permissions 
WHERE module IN ('content', 'products') AND name IN ('manage_categories', 'manage_brands', 'manage_banners', 'manage_pages', 'manage_reviews', 'manage_blog', 'view_products');

-- Assign Permissions to Support Staff
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
SELECT 
    (SELECT id FROM user_roles WHERE name = 'support_staff'),
    id 
FROM permissions 
WHERE module IN ('support', 'orders', 'users') AND name IN ('view_orders', 'manage_orders', 'process_refunds', 'manage_tickets', 'view_customer_data', 'send_notifications', 'view_users');

-- Assign Permissions to Vendor
INSERT INTO `role_permissions` (`role_id`, `permission_id`)
SELECT 
    (SELECT id FROM user_roles WHERE name = 'vendor'),
    id 
FROM permissions 
WHERE name IN ('manage_products', 'view_products', 'manage_inventory', 'view_orders', 'view_analytics');

-- Assign default customer role to existing users
INSERT INTO `user_role_assignments` (`user_id`, `role_id`, `assigned_by`)
SELECT 
    u.id,
    (SELECT id FROM user_roles WHERE name = 'customer'),
    (SELECT id FROM users WHERE email = 'admin@pavitra.com' LIMIT 1)
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM user_role_assignments WHERE user_id = u.id
);

-- Assign super_admin role to the main admin user
INSERT INTO `user_role_assignments` (`user_id`, `role_id`, `assigned_by`)
SELECT 
    id,
    (SELECT id FROM user_roles WHERE name = 'super_admin'),
    id
FROM users 
WHERE email = 'admin@pavitra.com'
ON DUPLICATE KEY UPDATE role_id = VALUES(role_id);

SET FOREIGN_KEY_CHECKS = 1;

SELECT 'User roles and permissions system initialized successfully!' as status;
