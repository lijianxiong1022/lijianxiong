#!/bin/bash
# 一键部署脚本 - 在服务器上执行
# 使用方法：将脚本上传到服务器后执行 bash 一键部署脚本.sh

set -e

echo "=========================================="
echo "订单系统 - 一键部署脚本"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量（请根据实际情况修改）
PROJECT_DIR="/var/www/order-system"
DB_NAME="order_system"
DB_USER="order_user"
# DB_PASSWORD 将在脚本中提示输入

echo -e "${YELLOW}步骤1: 检查环境...${NC}"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到python3，请先安装${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python3: $(python3 --version)${NC}"

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}错误: 未找到pip3，请先安装${NC}"
    exit 1
fi
echo -e "${GREEN}✓ pip3 已安装${NC}"

# 检查MySQL
if ! command -v mysql &> /dev/null; then
    echo -e "${RED}错误: 未找到mysql客户端，请先安装${NC}"
    exit 1
fi
echo -e "${GREEN}✓ MySQL客户端已安装${NC}"

echo ""
echo -e "${YELLOW}步骤2: 配置数据库...${NC}"

# 读取数据库密码
read -sp "请输入MySQL root密码: " MYSQL_ROOT_PASSWORD
echo ""
read -sp "请输入数据库用户密码（将创建用户 $DB_USER）: " DB_PASSWORD
echo ""

# 创建数据库和用户
echo "创建数据库和用户..."
mysql -u root -p"$MYSQL_ROOT_PASSWORD" << EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 数据库配置成功${NC}"
else
    echo -e "${RED}✗ 数据库配置失败${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}步骤3: 创建项目目录...${NC}"

sudo mkdir -p "$PROJECT_DIR"
sudo chown -R $USER:$USER "$PROJECT_DIR"
echo -e "${GREEN}✓ 项目目录已创建: $PROJECT_DIR${NC}"

echo ""
echo -e "${YELLOW}步骤4: 配置Git仓库...${NC}"
echo "请选择Git仓库方式："
echo "1) 已有远程仓库（GitHub/Gitee等）"
echo "2) 在服务器上创建Git仓库"
read -p "请选择 (1/2): " GIT_CHOICE

if [ "$GIT_CHOICE" = "1" ]; then
    read -p "请输入Git仓库地址: " GIT_REPO_URL
    if [ -d "$PROJECT_DIR/.git" ]; then
        cd "$PROJECT_DIR"
        git pull origin main || git pull origin master
    else
        git clone "$GIT_REPO_URL" "$PROJECT_DIR"
    fi
elif [ "$GIT_CHOICE" = "2" ]; then
    echo "将在服务器上创建Git仓库，请稍后在本地配置远程仓库"
    # 这里可以创建裸仓库
fi

echo ""
echo -e "${YELLOW}步骤5: 配置生产环境...${NC}"

cd "$PROJECT_DIR/backend"

# 生成JWT密钥
JWT_SECRET=$(openssl rand -hex 32)

# 创建生产环境配置
cat > .env.production << EOF
# 生产环境配置
USE_SQLITE=False
DB_HOST=localhost
DB_PORT=3306
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_NAME=$DB_NAME

JWT_SECRET_KEY=$JWT_SECRET
JWT_ACCESS_TOKEN_EXPIRES=86400

FLASK_ENV=production
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
EOF

echo -e "${GREEN}✓ 生产环境配置已创建${NC}"

echo ""
echo -e "${YELLOW}步骤6: 安装Python依赖...${NC}"
pip3 install --user -r requirements.txt
echo -e "${GREEN}✓ 依赖安装完成${NC}"

echo ""
echo -e "${YELLOW}步骤7: 初始化数据库...${NC}"
export FLASK_ENV=production
python3 init_db.py
echo -e "${GREEN}✓ 数据库初始化完成${NC}"

echo ""
echo -e "${YELLOW}步骤8: 创建上传目录...${NC}"
mkdir -p uploads/exception_orders
chmod -R 755 uploads
echo -e "${GREEN}✓ 上传目录已创建${NC}"

echo ""
echo -e "${YELLOW}步骤9: 配置Systemd服务...${NC}"
if [ -f "systemd/order-system.service" ]; then
    sudo cp systemd/order-system.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable order-system
    sudo systemctl start order-system
    echo -e "${GREEN}✓ 服务已启动${NC}"
else
    echo -e "${YELLOW}⚠ 未找到服务文件，请手动配置${NC}"
fi

echo ""
echo -e "${YELLOW}步骤10: 配置Nginx（可选）...${NC}"
read -p "是否配置Nginx? (y/n): " CONFIGURE_NGINX
if [ "$CONFIGURE_NGINX" = "y" ]; then
    if [ -f "../nginx/order-system.conf" ]; then
        sudo cp ../nginx/order-system.conf /etc/nginx/conf.d/
        read -p "请输入域名或IP（用于Nginx配置）: " SERVER_NAME
        sudo sed -i "s/your_domain.com/$SERVER_NAME/g" /etc/nginx/conf.d/order-system.conf
        sudo nginx -t && sudo systemctl restart nginx
        echo -e "${GREEN}✓ Nginx已配置${NC}"
    else
        echo -e "${YELLOW}⚠ 未找到Nginx配置文件${NC}"
    fi
fi

echo ""
echo "=========================================="
echo -e "${GREEN}部署完成！${NC}"
echo "=========================================="
echo ""
echo "服务状态:"
sudo systemctl status order-system --no-pager -l || echo "服务未配置"
echo ""
echo "测试API:"
echo "curl http://localhost:5000/api/v1/user/register"
echo ""

