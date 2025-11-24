@echo off
chcp 65001 >nul
echo ========================================
echo 创建环境配置文件
echo ========================================
echo.

echo 请输入数据库配置信息（直接回车使用默认值）:
echo.

set /p DB_HOST="数据库主机 [localhost]: "
if "%DB_HOST%"=="" set DB_HOST=localhost

set /p DB_PORT="数据库端口 [3306]: "
if "%DB_PORT%"=="" set DB_PORT=3306

set /p DB_USER="数据库用户名 [root]: "
if "%DB_USER%"=="" set DB_USER=root

set /p DB_PASSWORD="数据库密码: "

set /p DB_NAME="数据库名称 [order_system]: "
if "%DB_NAME%"=="" set DB_NAME=order_system

echo.
echo 正在创建.env文件...

(
echo # 数据库配置
echo DB_HOST=%DB_HOST%
echo DB_PORT=%DB_PORT%
echo DB_USER=%DB_USER%
echo DB_PASSWORD=%DB_PASSWORD%
echo DB_NAME=%DB_NAME%
echo.
echo # JWT配置
echo JWT_SECRET_KEY=dev-secret-key-change-this-in-production-2023
echo JWT_ACCESS_TOKEN_EXPIRES=86400
echo.
echo # Flask配置
echo FLASK_ENV=development
echo FLASK_DEBUG=True
echo FLASK_HOST=0.0.0.0
echo FLASK_PORT=5000
) > .env

echo.
echo [OK] .env 文件已创建！
echo.
echo 下一步：
echo 1. 确保MySQL服务已启动
echo 2. 运行: python init_db.py  (初始化数据库)
echo 3. 运行: python app.py      (启动服务)
echo.
pause

