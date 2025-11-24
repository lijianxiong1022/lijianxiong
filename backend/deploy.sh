#!/bin/bash
# 服务器部署脚本

set -e  # 遇到错误立即退出

echo "=========================================="
echo "开始部署订单系统..."
echo "=========================================="

# 进入项目目录
cd "$(dirname "$0")"
PROJECT_DIR=$(pwd)
BACKEND_DIR="$PROJECT_DIR/backend"

echo "项目目录: $PROJECT_DIR"
echo "后端目录: $BACKEND_DIR"

# 检查Python环境
echo ""
echo "检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到python3，请先安装Python 3"
    exit 1
fi
python3 --version

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "错误: 未找到pip3，请先安装pip"
    exit 1
fi

# 进入后端目录
cd "$BACKEND_DIR"

# 检查生产环境配置文件
if [ ! -f ".env.production" ]; then
    echo ""
    echo "警告: 未找到 .env.production 文件"
    echo "请创建生产环境配置文件："
    echo "  cp .env.production.example .env.production"
    echo "  然后编辑 .env.production 填入正确的配置"
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 加载生产环境配置
if [ -f ".env.production" ]; then
    echo ""
    echo "加载生产环境配置..."
    export $(cat .env.production | grep -v '^#' | xargs)
fi

# 安装/更新依赖
echo ""
echo "安装Python依赖..."
pip3 install -r requirements.txt --user

# 检查数据库连接
echo ""
echo "检查数据库连接..."
python3 << EOF
import os
import sys
from dotenv import load_dotenv

# 加载生产环境配置
if os.path.exists('.env.production'):
    load_dotenv('.env.production')

try:
    from app import create_app
    from models import db
    
    app = create_app()
    with app.app_context():
        # 测试数据库连接
        db.session.execute('SELECT 1')
        print("✓ 数据库连接成功")
except Exception as e:
    print(f"✗ 数据库连接失败: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo "错误: 数据库连接失败，请检查配置"
    exit 1
fi

# 初始化数据库（如果需要）
echo ""
read -p "是否需要初始化数据库表？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "初始化数据库..."
    python3 init_db.py
fi

# 创建上传目录
echo ""
echo "创建上传目录..."
mkdir -p uploads/exception_orders
chmod -R 755 uploads

# 重启服务（如果使用systemd）
if systemctl is-active --quiet order-system 2>/dev/null; then
    echo ""
    echo "重启服务..."
    sudo systemctl restart order-system
    sleep 2
    sudo systemctl status order-system --no-pager
elif systemctl list-unit-files | grep -q order-system; then
    echo ""
    echo "启动服务..."
    sudo systemctl start order-system
    sleep 2
    sudo systemctl status order-system --no-pager
else
    echo ""
    echo "提示: 未找到systemd服务，请手动启动应用"
    echo "运行: python3 app.py"
fi

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "检查服务状态:"
echo "  sudo systemctl status order-system"
echo ""
echo "查看日志:"
echo "  sudo journalctl -u order-system -f"
echo ""
echo "测试API:"
echo "  curl http://localhost:5000/api/v1/user/register"
echo ""

