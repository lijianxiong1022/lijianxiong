-- 数据库初始化脚本
-- 在MySQL中执行此脚本创建数据库和用户

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS order_system DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建数据库用户（请修改密码）
-- 注意：请将 'your_password_here' 替换为实际密码
CREATE USER IF NOT EXISTS 'order_user'@'localhost' IDENTIFIED BY 'your_password_here';

-- 授予权限
GRANT ALL PRIVILEGES ON order_system.* TO 'order_user'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 显示创建结果
SELECT 'Database and user created successfully!' AS result;

