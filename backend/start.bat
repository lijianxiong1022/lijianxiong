@echo off
chcp 65001 >nul
echo ========================================
echo 启动报单系统后端服务
echo ========================================
echo.

REM 检查.env文件是否存在
if not exist .env (
    echo ⚠️  未找到.env配置文件
    echo 正在运行配置脚本...
    python setup_env.py
    echo.
)

REM 检查数据库是否已初始化
echo 检查数据库连接...
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.engine.connect(); print('✅ 数据库连接成功')" 2>nul
if errorlevel 1 (
    echo ⚠️  数据库连接失败，请检查配置
    echo 是否要初始化数据库？(Y/N)
    set /p init_db=
    if /i "%init_db%"=="Y" (
        python init_db.py
    )
    echo.
)

echo 启动Flask服务...
echo 服务地址: http://localhost:5000
echo 按 Ctrl+C 停止服务
echo.
python app.py

pause

