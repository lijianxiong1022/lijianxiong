#!/bin/bash
# 备份服务器文件到本地的脚本

echo "=========================================="
echo "   备份服务器文件到本地"
echo "=========================================="
echo ""

# 配置
SERVER="root@175.24.47.45"
REMOTE_PATH="/var/www/order-system"
BACKUP_DIR="backup/$(date +%Y%m%d_%H%M%S)"

# 创建备份目录
mkdir -p "$BACKUP_DIR"
echo "📁 备份目录: $BACKUP_DIR"

echo ""
echo "[1/2] 下载服务器文件..."
# 下载整个项目（排除.git等）
rsync -avz --exclude='.git' --exclude='*.pyc' --exclude='__pycache__' \
    $SERVER:$REMOTE_PATH/ "$BACKUP_DIR/"

if [ $? -eq 0 ]; then
    echo "✅ 文件下载完成"
else
    echo "❌ 下载失败"
    exit 1
fi

echo ""
echo "[2/2] 生成差异报告..."
# 比较关键文件
if [ -f "all_pages.html" ]; then
    echo "比较 all_pages.html..."
    diff -u all_pages.html "$BACKUP_DIR/all_pages.html" > "$BACKUP_DIR/diff_all_pages.html" 2>&1 || true
fi

if [ -f "admin.html" ]; then
    echo "比较 admin.html..."
    diff -u admin.html "$BACKUP_DIR/admin.html" > "$BACKUP_DIR/diff_admin.html" 2>&1 || true
fi

echo ""
echo "=========================================="
echo "✅ 备份完成！"
echo "📁 备份位置: $BACKUP_DIR"
echo "=========================================="

