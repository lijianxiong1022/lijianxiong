"""
检查环境配置脚本
检查所有必要的配置和依赖
"""
import os
import sys

# 设置控制台编码为UTF-8（Windows）
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

def check_python():
    """检查Python版本"""
    print("检查Python版本...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"[OK] Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"[ERROR] Python版本过低，需要3.8+，当前: {version.major}.{version.minor}")
        return False

def check_dependencies():
    """检查依赖包"""
    print("\n检查Python依赖包...")
    required_packages = [
        'flask', 'flask_sqlalchemy', 'flask_jwt_extended', 
        'flask_cors', 'pymysql', 'dotenv'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"[OK] {package}")
        except ImportError:
            print(f"[ERROR] {package} 未安装")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  缺少依赖包，请运行: pip install -r requirements.txt")
        return False
    return True

def check_env_file():
    """检查.env文件"""
    print("\n检查环境配置文件...")
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        print("[OK] .env 文件存在")
        return True
    else:
        print("[ERROR] .env 文件不存在")
        print("   请运行: python setup_env.py")
        return False

def check_database():
    """检查数据库连接"""
    print("\n检查数据库连接...")
    try:
        from app import create_app
        from models import db
        
        app = create_app()
        with app.app_context():
            # 尝试连接数据库
            db.engine.connect()
            print("[OK] 数据库连接成功")
            
            # 检查表是否存在
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = ['users', 'orders', 'non_members', 'transactions', 'admins']
            missing_tables = [t for t in required_tables if t not in tables]
            
            if missing_tables:
                print(f"[WARNING] 缺少数据表: {', '.join(missing_tables)}")
                print("   请运行: python init_db.py")
                return False
            else:
                print("[OK] 数据库表已创建")
                return True
                
    except Exception as e:
        print(f"[ERROR] 数据库连接失败: {str(e)}")
        print("   请检查:")
        print("   1. MySQL服务是否运行")
        print("   2. .env文件中的数据库配置是否正确")
        print("   3. 数据库是否已创建")
        return False

def main():
    print("=" * 50)
    print("环境检查")
    print("=" * 50)
    
    results = []
    results.append(check_python())
    results.append(check_dependencies())
    results.append(check_env_file())
    results.append(check_database())
    
    print("\n" + "=" * 50)
    if all(results):
        print("[OK] 所有检查通过！可以启动服务了")
        print("\n启动命令: python app.py")
    else:
        print("[ERROR] 部分检查未通过，请根据上述提示修复问题")
    print("=" * 50)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n[ERROR] 检查过程中出错: {e}")

