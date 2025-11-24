#!/bin/bash
# 同步云端修改到本地的脚本

echo "=========================================="
echo "   同步云端修改到本地"
echo "=========================================="
echo ""

# 配置
SERVER="root@175.24.47.45"
REMOTE_PATH="/var/www/order-system"
LOCAL_PATH="."

# 检查是否在Git仓库中
if [ ! -d ".git" ]; then
    echo "❌ 当前目录不是Git仓库"
    exit 1
fi

echo "[1/3] 检查服务器是否有未提交的修改..."
# 检查服务器是否有未提交的修改
HAS_CHANGES=$(ssh $SERVER "cd $REMOTE_PATH && git status --porcelain | wc -l")

if [ "$HAS_CHANGES" -gt 0 ]; then
    echo "⚠️  服务器有未提交的修改"
    read -p "是否提交并推送这些修改？(y/n): " confirm
    if [ "$confirm" = "y" ]; then
        echo "正在提交服务器修改..."
        ssh $SERVER "cd $REMOTE_PATH && git add . && git commit -m '云端修改: $(date +%Y-%m-%d\ %H:%M:%S)' && git push origin master"
        if [ $? -eq 0 ]; then
            echo "✅ 服务器修改已提交并推送"
        else
            echo "❌ 提交失败，请手动处理"
            exit 1
        fi
    else
        echo "⚠️  跳过提交，继续同步..."
    fi
else
    echo "✅ 服务器没有未提交的修改"
fi

echo ""
echo "[2/3] 从GitHub拉取最新代码..."
git pull origin master

if [ $? -eq 0 ]; then
    echo "✅ 本地代码已更新"
else
    echo "❌ 拉取失败"
    exit 1
fi

echo ""
echo "[3/3] 检查本地和服务器文件差异..."
# 比较关键文件
FILES=("all_pages.html" "admin.html" "backend/api/orders.py")

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "检查: $file"
        # 这里可以添加具体的比较逻辑
    fi
done

echo ""
echo "=========================================="
echo "✅ 同步完成！"
echo "=========================================="

