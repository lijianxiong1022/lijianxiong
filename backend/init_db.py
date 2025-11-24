"""
初始化数据库脚本
创建默认管理员账户和平台用户
"""
from app import create_app
from models import db, Admin, User
from utils import hash_password, hash_pay_password

def init_database():
    app = create_app()
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        
        # 创建默认管理员账户
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = Admin(
                username='admin',
                password=hash_password('admin123'),
                name='管理员',
                role='super_admin'
            )
            db.session.add(admin)
            db.session.commit()
            print('[OK] 默认管理员账户创建成功')
            print('   用户名: admin')
            print('   密码: admin123')
        else:
            print('[INFO] 管理员账户已存在')
        
        # 创建平台用户（推广码888888，作为平台代理的上级）
        platform_user = User.query.filter_by(promo_code='888888').first()
        if not platform_user:
            platform_user = User(
                promo_code='888888',
                name='平台',
                phone='00000000000',  # 虚拟手机号
                password=hash_password('platform888888'),  # 平台密码
                pay_password=hash_pay_password('888888'),  # 支付密码
                user_type='agent',  # 平台本身是代理类型
                parent_id=None,  # 平台没有上级
                points=0
            )
            db.session.add(platform_user)
            db.session.commit()
            print('[OK] 平台用户创建成功')
            print('   推广码: 888888')
            print('   名称: 平台')
        else:
            print('[INFO] 平台用户已存在')
        
        print('[OK] 数据库初始化完成')

if __name__ == '__main__':
    init_database()

