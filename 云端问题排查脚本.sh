#!/bin/bash
# 云端问题排查脚本 - 自动检查常见问题

echo "=========================================="
echo "   云端问题排查工具"
echo "=========================================="
echo ""

SERVER="root@175.24.47.45"
REMOTE_PATH="/var/www/order-system"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_service() {
    echo "[1/8] 检查服务状态..."
    STATUS=$(ssh $SERVER "systemctl is-active order-system" 2>/dev/null)
    if [ "$STATUS" = "active" ]; then
        echo -e "${GREEN}✅ 服务运行中${NC}"
    else
        echo -e "${RED}❌ 服务未运行${NC}"
        echo "   尝试启动: systemctl start order-system"
    fi
    echo ""
}

check_code_version() {
    echo "[2/8] 检查代码版本..."
    LOCAL_VERSION=$(git log -1 --format="%H" 2>/dev/null)
    REMOTE_VERSION=$(ssh $SERVER "cd $REMOTE_PATH && git log -1 --format='%H'" 2>/dev/null)
    
    if [ "$LOCAL_VERSION" = "$REMOTE_VERSION" ]; then
        echo -e "${GREEN}✅ 代码版本一致${NC}"
    else
        echo -e "${YELLOW}⚠️  代码版本不一致${NC}"
        echo "   本地: $LOCAL_VERSION"
        echo "   服务器: $REMOTE_VERSION"
    fi
    echo ""
}

check_config() {
    echo "[3/8] 检查配置文件..."
    if ssh $SERVER "test -f $REMOTE_PATH/backend/.env.production"; then
        echo -e "${GREEN}✅ 配置文件存在${NC}"
    else
        echo -e "${RED}❌ 配置文件不存在${NC}"
    fi
    echo ""
}

check_api() {
    echo "[4/8] 检查API接口..."
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://175.24.47.45/api/v1/user/register 2>/dev/null)
    if [ "$RESPONSE" = "405" ] || [ "$RESPONSE" = "400" ]; then
        echo -e "${GREEN}✅ API可访问 (HTTP $RESPONSE)${NC}"
    elif [ "$RESPONSE" = "404" ]; then
        echo -e "${RED}❌ API返回404${NC}"
    else
        echo -e "${YELLOW}⚠️  API响应: HTTP $RESPONSE${NC}"
    fi
    echo ""
}

check_files() {
    echo "[5/8] 检查关键文件..."
    FILES=("all_pages.html" "admin.html" "backend/app.py")
    for file in "${FILES[@]}"; do
        if ssh $SERVER "test -f $REMOTE_PATH/$file"; then
            echo -e "${GREEN}✅ $file 存在${NC}"
        else
            echo -e "${RED}❌ $file 不存在${NC}"
        fi
    done
    echo ""
}

check_database() {
    echo "[6/8] 检查数据库连接..."
    DB_TEST=$(ssh $SERVER "mysql -u order_user -pljx19921022.. order_system -e 'SELECT 1;' 2>&1" | grep -v "Warning")
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 数据库连接正常${NC}"
    else
        echo -e "${RED}❌ 数据库连接失败${NC}"
    fi
    echo ""
}

check_logs() {
    echo "[7/8] 检查最近错误日志..."
    ERRORS=$(ssh $SERVER "journalctl -u order-system -n 20 --no-pager | grep -i 'error\|exception\|traceback' | tail -5")
    if [ -z "$ERRORS" ]; then
        echo -e "${GREEN}✅ 最近没有错误日志${NC}"
    else
        echo -e "${YELLOW}⚠️  发现错误日志:${NC}"
        echo "$ERRORS"
    fi
    echo ""
}

check_port() {
    echo "[8/8] 检查端口监听..."
    PORT_CHECK=$(ssh $SERVER "netstat -tlnp | grep ':5000'")
    if [ -n "$PORT_CHECK" ]; then
        echo -e "${GREEN}✅ 端口5000正在监听${NC}"
    else
        echo -e "${RED}❌ 端口5000未监听${NC}"
    fi
    echo ""
}

# 执行所有检查
check_service
check_code_version
check_config
check_api
check_files
check_database
check_logs
check_port

echo "=========================================="
echo "✅ 排查完成"
echo "=========================================="

