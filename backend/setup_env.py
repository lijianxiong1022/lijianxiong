"""
环境配置脚本
帮助用户创建.env配置文件
"""
import os

def create_env_file():
    print("=" * 50)
    print("环境配置设置")
    print("=" * 50)
    
    # 读取示例文件
    example_path = os.path.join(os.path.dirname(__file__), 'env.example')
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if os.path.exists(env_path):
        print("⚠️  .env 文件已存在")
        response = input("是否要覆盖现有配置？(y/n): ")
        if response.lower() != 'y':
            print("已取消")
            return
    
    print("\n请输入数据库配置信息：")
    
    db_host = input("数据库主机 [localhost]: ").strip() or "localhost"
    db_port = input("数据库端口 [3306]: ").strip() or "3306"
    db_user = input("数据库用户名 [root]: ").strip() or "root"
    db_password = input("数据库密码: ").strip()
    db_name = input("数据库名称 [order_system]: ").strip() or "order_system"
    
    print("\n请输入JWT配置：")
    jwt_secret = input("JWT密钥 [随机生成]: ").strip()
    if not jwt_secret:
        import secrets
        jwt_secret = secrets.token_urlsafe(32)
        print(f"已生成随机密钥: {jwt_secret[:20]}...")
    
    # 创建.env文件内容
    env_content = f"""# 数据库配置
DB_HOST={db_host}
DB_PORT={db_port}
DB_USER={db_user}
DB_PASSWORD={db_password}
DB_NAME={db_name}

# JWT配置
JWT_SECRET_KEY={jwt_secret}
JWT_ACCESS_TOKEN_EXPIRES=86400

# Flask配置
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
"""
    
    # 写入文件
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"\n✅ .env 文件已创建: {env_path}")
    print("\n下一步：")
    print("1. 确保MySQL服务已启动")
    print("2. 运行: python init_db.py  (初始化数据库)")
    print("3. 运行: python app.py      (启动服务)")

if __name__ == '__main__':
    try:
        create_env_file()
    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n❌ 错误: {e}")

