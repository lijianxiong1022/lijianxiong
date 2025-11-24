import os
from datetime import timedelta
from dotenv import load_dotenv

# 根据环境加载不同的配置文件
# 如果存在 .env.production 且 FLASK_ENV=production，则加载生产配置
# 否则加载开发配置 .env
if os.getenv('FLASK_ENV') == 'production' and os.path.exists(os.path.join(os.path.dirname(__file__), '.env.production')):
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env.production'))
else:
    load_dotenv()

class Config:
    # 数据库配置
    USE_SQLITE = os.getenv('USE_SQLITE', 'False').lower() == 'true'
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'order_system')
    
    # 构建数据库URI
    if USE_SQLITE:
        # 使用SQLite（开发/测试环境，无需安装MySQL）
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'order_system.db')}"
    else:
        # 使用MySQL（生产环境）
        if DB_PASSWORD:
            SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
        else:
            SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv('FLASK_DEBUG', 'True') == 'True'
    
    # JWT配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
    jwt_expires = os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '86400')
    try:
        JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(jwt_expires))
    except:
        JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=86400)
    
    # Flask配置
    DEBUG = os.getenv('FLASK_DEBUG', 'True') == 'True'
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    try:
        PORT = int(os.getenv('FLASK_PORT', '5000'))
    except:
        PORT = 5000

