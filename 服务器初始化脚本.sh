#!/bin/bash
# 服务器初始化脚本 - 在服务器上首次执行
# 安装必要的软件和配置环境

set -e

echo "=========================================="
echo "服务器环境初始化"
echo "=========================================="

# 更新系统
echo "更新系统包..."
sudo yum update -y

# 安装Python 3
echo "检查Python 3..."
if ! command -v python3 &> /dev/null; then
    echo "安装Python 3..."
    sudo yum install -y python3 python3-pip python3-devel
else
    echo "Python 3已安装: $(python3 --version)"
fi

# 安装MySQL客户端和开发库
echo "安装MySQL客户端..."
sudo yum install -y mysql mysql-devel

# 安装Git
echo "检查Git..."
if ! command -v git &> /dev/null; then
    echo "安装Git..."
    sudo yum install -y git
else
    echo "Git已安装: $(git --version)"
fi

# 安装Nginx（可选）
read -p "是否安装Nginx? (y/n): " INSTALL_NGINX
if [ "$INSTALL_NGINX" = "y" ]; then
    if ! command -v nginx &> /dev/null; then
        sudo yum install -y nginx
        sudo systemctl enable nginx
        sudo systemctl start nginx
        echo "Nginx已安装并启动"
    else
        echo "Nginx已安装"
    fi
fi

# 配置防火墙
read -p "是否配置防火墙开放80端口? (y/n): " CONFIGURE_FIREWALL
if [ "$CONFIGURE_FIREWALL" = "y" ]; then
    sudo firewall-cmd --permanent --add-service=http
    sudo firewall-cmd --permanent --add-service=https
    sudo firewall-cmd --reload
    echo "防火墙已配置"
fi

# 创建项目目录
echo "创建项目目录..."
sudo mkdir -p /var/www/order-system
sudo chown -R $USER:$USER /var/www/order-system

echo ""
echo "=========================================="
echo "初始化完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 上传代码到服务器"
echo "2. 运行部署脚本"

