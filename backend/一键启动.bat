@echo off
chcp 65001 >nul
title 报单系统后端服务
color 0A

echo.
echo ========================================
echo   报单系统后端服务启动器
echo ========================================
echo.

REM 检查.env文件
if not exist .env (
    echo [警告] 未找到.env配置文件
    echo.
    echo 请先创建.env文件，内容如下：
    echo.
    echo DB_HOST=localhost
    echo DB_PORT=3306
    echo DB_USER=root
    echo DB_PASSWORD=你的MySQL密码
    echo DB_NAME=order_system
    echo.
    echo JWT_SECRET_KEY=dev-secret-key-change-this-in-production-2023
    echo JWT_ACCESS_TOKEN_EXPIRES=86400
    echo.
    echo FLASK_ENV=development
    echo FLASK_DEBUG=True
    echo FLASK_HOST=0.0.0.0
    echo FLASK_PORT=5000
    echo.
    echo 如果MySQL没有密码，DB_PASSWORD留空即可
    echo.
    pause
    exit /b 1
)

echo [1/3] 检查环境配置...
python check_setup.py
if errorlevel 1 (
    echo.
    echo [错误] 环境检查未通过，请根据提示修复问题
    pause
    exit /b 1
)

echo.
echo [2/3] 检查数据库...
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.engine.connect(); print('[OK] 数据库连接成功')" 2>nul
if errorlevel 1 (
    echo [警告] 数据库连接失败
    echo.
    set /p init_choice="是否要初始化数据库？(Y/N): "
    if /i "!init_choice!"=="Y" (
        echo 正在初始化数据库...
        python init_db.py
        if errorlevel 1 (
            echo [错误] 数据库初始化失败
            pause
            exit /b 1
        )
    ) else (
        echo 已取消，请手动运行: python init_db.py
        pause
        exit /b 1
    )
)

echo.
echo [3/3] 启动Flask服务...
echo.
echo ========================================
echo   服务地址: http://localhost:5000
echo   按 Ctrl+C 停止服务
echo ========================================
echo.

python app.py

pause

