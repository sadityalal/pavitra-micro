-- Create users with remote access from any host
CREATE USER IF NOT EXISTS 'pavitra_user'@'%' IDENTIFIED BY 'user123';
CREATE USER IF NOT EXISTS 'pavitra_app'@'%' IDENTIFIED BY 'app123';

-- Grant all privileges with remote access
GRANT ALL PRIVILEGES ON pavitra_trading.* TO 'pavitra_user'@'%' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON pavitra_trading.* TO 'pavitra_app'@'%' WITH GRANT OPTION;

-- Create super user for admin access
GRANT ALL PRIVILEGES ON *.* TO 'pavitra_user'@'%' WITH GRANT OPTION;

-- Apply changes
FLUSH PRIVILEGES;

-- Show final user permissions
SELECT user, host, authentication_string FROM mysql.user WHERE user LIKE 'pavitra%';
