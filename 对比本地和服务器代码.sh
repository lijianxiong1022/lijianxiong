#!/bin/bash
# 对比本地和服务器代码的脚本

echo "=========================================="
echo "   对比本地和服务器代码"
echo "=========================================="
echo ""

SERVER="root@175.24.47.45"
REMOTE_PATH="/var/www/order-system"

# 要对比的文件列表
FILES=(
    "all_pages.html"
    "admin.html"
    "backend/api/orders.py"
    "backend/api/settings.py"
    "backend/app.py"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "对比: $file"
        
        # 下载服务器文件到临时文件
        TEMP_FILE=$(mktemp)
        ssh $SERVER "cat $REMOTE_PATH/$file" > "$TEMP_FILE" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            # 对比文件
            if diff -q "$file" "$TEMP_FILE" > /dev/null 2>&1; then
                echo "  ✅ 文件相同"
            else
                echo "  ❌ 文件不同"
                echo "  差异详情:"
                diff -u "$file" "$TEMP_FILE" | head -20
                echo ""
            fi
        else
            echo "  ⚠️  无法下载服务器文件"
        fi
        
        rm -f "$TEMP_FILE"
        echo ""
    else
        echo "⚠️  本地文件不存在: $file"
        echo ""
    fi
done

echo "=========================================="
echo "✅ 对比完成"
echo "=========================================="

