-- 创建数据库
CREATE DATABASE IF NOT EXISTS order_system DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE order_system;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    promo_code VARCHAR(6) UNIQUE NOT NULL COMMENT '推广码（6位数字）',
    name VARCHAR(50) NOT NULL COMMENT '姓名',
    phone VARCHAR(11) UNIQUE NOT NULL COMMENT '手机号',
    password VARCHAR(255) NOT NULL COMMENT '登录密码（加密）',
    pay_password VARCHAR(255) NOT NULL COMMENT '支付密码（6位数字，加密）',
    user_type ENUM('ordinary', 'agent') DEFAULT 'ordinary' COMMENT '用户类型：普通会员/代理会员',
    parent_id INT COMMENT '上级用户ID',
    points DECIMAL(10,2) DEFAULT 0 COMMENT '金币余额',
    register_date DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_promo_code (promo_code),
    INDEX idx_phone (phone),
    INDEX idx_parent_id (parent_id),
    FOREIGN KEY (parent_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 非会员用户表
CREATE TABLE IF NOT EXISTS non_members (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL COMMENT '姓名',
    link VARCHAR(500) COMMENT '碰碰链接',
    owner_id INT NOT NULL COMMENT '所属用户ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_owner_id (owner_id),
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='非会员用户表';

-- 订单表
CREATE TABLE IF NOT EXISTS orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL COMMENT '报单用户ID',
    non_member_id INT COMMENT '非会员用户ID',
    settlement_date DATE NOT NULL COMMENT '报单日期',
    base_price DECIMAL(10,2) NOT NULL COMMENT '基础单价',
    discount_rate DECIMAL(5,2) DEFAULT 0 COMMENT '优惠折扣率',
    final_price DECIMAL(10,2) NOT NULL COMMENT '最终单价',
    quantity INT NOT NULL COMMENT '报单数量',
    total_points DECIMAL(10,2) NOT NULL COMMENT '消耗总金币',
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'approved' COMMENT '订单状态',
    exported BOOLEAN DEFAULT FALSE COMMENT '是否已导出',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_settlement_date (settlement_date),
    INDEX idx_status (status),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (non_member_id) REFERENCES non_members(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单表';

-- 交易记录表
CREATE TABLE IF NOT EXISTS transactions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    transaction_type ENUM('recharge', 'order_deduction', 'transfer_out', 'transfer_in', 'reward') NOT NULL,
    points_change DECIMAL(10,2) NOT NULL COMMENT '金币变动',
    balance DECIMAL(10,2) NOT NULL COMMENT '交易后余额',
    description VARCHAR(500) COMMENT '交易描述',
    related_user_id INT COMMENT '关联用户ID（转账时使用）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_transaction_type (transaction_type),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (related_user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='交易记录表';

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    setting_key VARCHAR(50) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL COMMENT 'JSON格式存储',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';

-- 管理员表
CREATE TABLE IF NOT EXISTS admins (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL COMMENT '加密密码',
    name VARCHAR(50) NOT NULL,
    role ENUM('super_admin', 'admin') DEFAULT 'admin',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管理员表';

-- 插入默认管理员（密码: admin123）
-- 注意：实际使用时需要先加密密码
INSERT INTO admins (username, password, name, role) 
VALUES ('admin', 'pbkdf2:sha256:600000$...', '管理员', 'super_admin')
ON DUPLICATE KEY UPDATE username=username;

