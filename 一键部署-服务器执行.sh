#!/bin/bash
# 一键部署脚本 - 在服务器上直接执行此脚本
# 使用方法：将此脚本上传到服务器，然后执行：bash 一键部署-服务器执行.sh

set -e

echo "=========================================="
echo "订单系统 - 一键部署脚本"
echo "服务器IP: 175.24.47.45"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 配置变量
PROJECT_DIR="/var/www/order-system"
DB_NAME="order_system"
DB_USER="order_user"
DB_PASSWORD="ljx19921022.."
MYSQL_ROOT_PASSWORD="19921022"
GIT_REPO="https://github.com/lijianxiong1022/lijianxiong.git"
SERVER_IP="175.24.47.45"

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}提示: 建议使用root用户执行此脚本${NC}"
fi

echo -e "${YELLOW}步骤1: 更新系统并安装必要软件...${NC}"
yum update -y || true
yum install -y python3 python3-pip python3-devel mysql mysql-devel gcc git nginx || {
    echo -e "${RED}✗ 软件安装失败，请检查网络连接${NC}"
    exit 1
}
echo -e "${GREEN}✓ 软件安装完成${NC}"

echo ""
echo -e "${YELLOW}步骤2: 创建项目目录...${NC}"
mkdir -p "$PROJECT_DIR"
chown -R $USER:$USER "$PROJECT_DIR" 2>/dev/null || true
echo -e "${GREEN}✓ 项目目录已创建${NC}"

echo ""
echo -e "${YELLOW}步骤3: 配置MySQL数据库...${NC}"
mysql -u root -p"$MYSQL_ROOT_PASSWORD" << EOF 2>/dev/null || {
    echo -e "${RED}✗ 数据库配置失败，请检查MySQL root密码${NC}"
    exit 1
}
CREATE DATABASE IF NOT EXISTS $DB_NAME DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
SELECT 'Database configured successfully!' AS result;
EOF
echo -e "${GREEN}✓ 数据库配置成功${NC}"

echo ""
echo -e "${YELLOW}步骤4: 从GitHub拉取代码...${NC}"
cd "$PROJECT_DIR"

if [ -d ".git" ]; then
    echo "代码已存在，拉取最新更新..."
    git pull origin master || git pull origin main || {
        echo -e "${YELLOW}⚠ 拉取失败，尝试重新克隆...${NC}"
        cd ..
        rm -rf "$PROJECT_DIR"
        mkdir -p "$PROJECT_DIR"
        cd "$PROJECT_DIR"
        git clone "$GIT_REPO" .
    }
else
    echo "克隆代码..."
    git clone "$GIT_REPO" . || {
        echo -e "${RED}✗ 代码克隆失败，请检查网络和Git仓库地址${NC}"
        exit 1
    }
fi

echo -e "${GREEN}✓ 代码拉取完成${NC}"

echo ""
echo -e "${YELLOW}步骤5: 配置生产环境...${NC}"
cd "$PROJECT_DIR/backend"

# 检查生产环境配置文件是否存在
if [ ! -f ".env.production" ]; then
    echo "创建生产环境配置文件..."
    cat > .env.production << ENVFILE
USE_SQLITE=False
DB_HOST=localhost
DB_PORT=3306
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_NAME=$DB_NAME

JWT_SECRET_KEY=prod-secret-key-2024-11-24-175244745-ljx19921022
JWT_ACCESS_TOKEN_EXPIRES=86400

FLASK_ENV=production
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
ENVFILE
    echo -e "${GREEN}✓ 生产环境配置已创建${NC}"
else
    echo -e "${GREEN}✓ 生产环境配置已存在${NC}"
fi

echo ""
echo -e "${YELLOW}步骤6: 安装Python依赖...${NC}"
pip3 install --user -r requirements.txt || {
    echo -e "${RED}✗ 依赖安装失败${NC}"
    exit 1
}
echo -e "${GREEN}✓ 依赖安装完成${NC}"

echo ""
echo -e "${YELLOW}步骤7: 初始化数据库...${NC}"
export FLASK_ENV=production
python3 init_db.py || {
    echo -e "${RED}✗ 数据库初始化失败${NC}"
    exit 1
}
echo -e "${GREEN}✓ 数据库初始化完成${NC}"

echo ""
echo -e "${YELLOW}步骤8: 创建上传目录...${NC}"
mkdir -p uploads/exception_orders
chmod -R 755 uploads
echo -e "${GREEN}✓ 上传目录已创建${NC}"

echo ""
echo -e "${YELLOW}步骤9: 配置Systemd服务...${NC}"
if [ -f "systemd/order-system.service" ]; then
    cp systemd/order-system.service /tmp/order-system.service
    sed -i "s|/path/to/order-system|$PROJECT_DIR/backend|g" /tmp/order-system.service
    sudo cp /tmp/order-system.service /etc/systemd/system/order-system.service
    sudo systemctl daemon-reload
    sudo systemctl enable order-system
    sudo systemctl start order-system
    sleep 3
    if sudo systemctl is-active --quiet order-system; then
        echo -e "${GREEN}✓ 服务已启动${NC}"
    else
        echo -e "${YELLOW}⚠ 服务启动可能失败，请检查日志${NC}"
        sudo systemctl status order-system --no-pager || true
    fi
else
    echo -e "${YELLOW}⚠ 未找到服务文件${NC}"
fi

echo ""
echo -e "${YELLOW}步骤10: 配置Nginx...${NC}"
if [ -f "../nginx/order-system.conf" ]; then
    sudo cp ../nginx/order-system.conf /etc/nginx/conf.d/order-system.conf
    sudo sed -i "s/your_domain.com/$SERVER_IP/g" /etc/nginx/conf.d/order-system.conf
    sudo nginx -t && sudo systemctl enable nginx && sudo systemctl start nginx || {
        echo -e "${YELLOW}⚠ Nginx配置或启动失败，请检查${NC}"
    }
    echo -e "${GREEN}✓ Nginx已配置并启动${NC}"
else
    echo -e "${YELLOW}⚠ 未找到Nginx配置文件${NC}"
fi

echo ""
echo -e "${YELLOW}步骤11: 配置防火墙...${NC}"
sudo firewall-cmd --permanent --add-service=http 2>/dev/null || true
sudo firewall-cmd --permanent --add-service=https 2>/dev/null || true
sudo firewall-cmd --reload 2>/dev/null || true
echo -e "${GREEN}✓ 防火墙已配置${NC}"

echo ""
echo "=========================================="
echo -e "${GREEN}部署完成！${NC}"
echo "=========================================="
echo ""
echo "服务信息："
echo "  前端地址: http://$SERVER_IP"
echo "  后台地址: http://$SERVER_IP/admin.html"
echo "  API地址: http://$SERVER_IP/api/v1"
echo ""
echo "默认管理员："
echo "  用户名: admin"
echo "  密码: admin123"
echo "  ⚠️ 请立即修改密码！"
echo ""
echo "常用命令："
echo "  查看服务状态: sudo systemctl status order-system"
echo "  查看服务日志: sudo journalctl -u order-system -f"
echo "  重启服务: sudo systemctl restart order-system"
echo ""

