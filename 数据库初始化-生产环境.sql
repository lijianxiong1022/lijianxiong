-- 数据库初始化脚本 - 生产环境
-- 根据你提供的信息自动生成
-- 在MySQL中执行此脚本创建数据库和用户

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS order_system DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建数据库用户
CREATE USER IF NOT EXISTS 'order_user'@'localhost' IDENTIFIED BY 'ljx19921022..';

-- 授予权限
GRANT ALL PRIVILEGES ON order_system.* TO 'order_user'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 显示创建结果
SELECT 'Database and user created successfully!' AS result;
SELECT 'Database: order_system' AS info;
SELECT 'User: order_user@localhost' AS info;

