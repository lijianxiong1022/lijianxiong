from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
import string

db = SQLAlchemy()

class User(db.Model):
    """用户表"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    promo_code = db.Column(db.String(6), unique=True, nullable=False, comment='推广码（6位数字）')
    name = db.Column(db.String(50), nullable=False, comment='姓名')
    phone = db.Column(db.String(11), unique=True, nullable=False, comment='手机号')
    password = db.Column(db.String(255), nullable=False, comment='登录密码（加密）')
    pay_password = db.Column(db.String(255), nullable=False, comment='支付密码（6位数字，加密）')
    user_type = db.Column(db.Enum('ordinary', 'agent'), default='ordinary', comment='用户类型')
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='上级用户ID')
    points = db.Column(db.Numeric(10, 2), default=0, comment='金币余额')
    register_date = db.Column(db.DateTime, default=datetime.now, comment='注册时间')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    parent = db.relationship('User', remote_side=[id], backref='children')
    
    @staticmethod
    def generate_promo_code():
        """生成6位数字推广码"""
        while True:
            code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            if not User.query.filter_by(promo_code=code).first():
                return code
    
    def to_dict(self):
        return {
            'id': self.id,
            'promoCode': self.promo_code,
            'name': self.name,
            'phone': self.phone[:3] + '****' + self.phone[-4:] if len(self.phone) == 11 else self.phone,
            'userType': self.user_type,
            'parentId': self.parent_id,
            'points': float(self.points),
            'registerDate': self.register_date.strftime('%Y-%m-%d') if self.register_date else None
        }

class NonMember(db.Model):
    """非会员用户表"""
    __tablename__ = 'non_members'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, comment='姓名')
    link = db.Column(db.String(500), nullable=True, comment='碰碰链接')
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='所属用户ID')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    owner = db.relationship('User', backref='non_members')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'link': self.link,
            'ownerId': self.owner_id,
            'createdAt': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class Order(db.Model):
    """订单表"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='报单用户ID')
    non_member_id = db.Column(db.Integer, db.ForeignKey('non_members.id'), nullable=True, comment='非会员用户ID')
    settlement_date = db.Column(db.Date, nullable=False, comment='报单日期')
    base_price = db.Column(db.Numeric(10, 2), nullable=False, comment='基础单价')
    discount_rate = db.Column(db.Numeric(5, 2), default=0, comment='优惠折扣率')
    final_price = db.Column(db.Numeric(10, 2), nullable=False, comment='最终单价')
    quantity = db.Column(db.Integer, nullable=False, comment='报单数量')
    total_points = db.Column(db.Numeric(10, 2), nullable=False, comment='消耗总金币')
    status = db.Column(db.Enum('pending', 'approved', 'rejected'), default='pending', comment='订单状态')
    exported = db.Column(db.Boolean, default=False, comment='是否已导出')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    user = db.relationship('User', backref='orders')
    non_member = db.relationship('NonMember', backref='orders')
    exception_order = db.relationship('ExceptionOrder', backref='order', uselist=False)
    
    def to_dict(self):
        from models import NonMember
        nonmember = NonMember.query.get(self.non_member_id) if self.non_member_id else None
        return {
            'id': self.id,
            'userId': self.user_id,
            'nonMemberId': self.non_member_id,
            'nonMemberName': nonmember.name if nonmember else None,
            'nonMemberLink': nonmember.link if nonmember else None,
            'settlementDate': self.settlement_date.strftime('%Y-%m-%d') if self.settlement_date else None,
            'basePrice': float(self.base_price),
            'discountRate': float(self.discount_rate),
            'finalPrice': float(self.final_price),
            'quantity': self.quantity,
            'totalPoints': float(self.total_points),
            'points': float(self.total_points),  # 兼容字段
            'status': self.status,
            'exported': self.exported,
            'createdAt': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'hasException': self.exception_order is not None,
            'exceptionStatus': self.exception_order.status if self.exception_order else None
        }

class Transaction(db.Model):
    """交易记录表"""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transaction_type = db.Column(db.Enum('recharge', 'order_deduction', 'transfer_out', 'transfer_in', 'reward'), nullable=False)
    points_change = db.Column(db.Numeric(10, 2), nullable=False, comment='金币变动')
    balance = db.Column(db.Numeric(10, 2), nullable=False, comment='交易后余额')
    description = db.Column(db.String(500), nullable=True, comment='交易描述')
    related_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='关联用户ID')
    unit_price = db.Column(db.Numeric(10, 2), nullable=True, comment='转账单价（元/金币），仅用于transfer_out类型')
    actual_cash_amount = db.Column(db.Numeric(10, 2), nullable=True, comment='实际支付的现金金额（元），仅用于recharge类型')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    user = db.relationship('User', foreign_keys=[user_id], backref='transactions')
    related_user = db.relationship('User', foreign_keys=[related_user_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'transactionType': self.transaction_type,
            'pointsChange': float(self.points_change),
            'balance': float(self.balance),
            'description': self.description,
            'relatedUserId': self.related_user_id,
            'unitPrice': float(self.unit_price) if self.unit_price else None,
            'actualCashAmount': float(self.actual_cash_amount) if self.actual_cash_amount else None,
            'createdAt': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class SystemSetting(db.Model):
    """系统配置表"""
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    setting_key = db.Column(db.String(50), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=False, comment='JSON格式存储')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class ExceptionOrder(db.Model):
    """异常订单表"""
    __tablename__ = 'exception_orders'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, unique=True, comment='关联订单ID')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='提交用户ID')
    description = db.Column(db.Text, nullable=False, comment='异常说明')
    image_urls = db.Column(db.Text, nullable=True, comment='图片URL列表（JSON格式）')
    status = db.Column(db.Enum('pending', 'exported'), default='pending', comment='异常订单状态')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    user = db.relationship('User', backref='exception_orders')
    
    def to_dict(self):
        import json
        image_list = []
        if self.image_urls:
            try:
                image_list = json.loads(self.image_urls)
            except:
                image_list = []
        return {
            'id': self.id,
            'orderId': self.order_id,
            'userId': self.user_id,
            'description': self.description,
            'imageUrls': image_list,
            'status': self.status,
            'createdAt': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class Admin(db.Model):
    """管理员表"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False, comment='加密密码')
    name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.Enum('super_admin', 'admin'), default='admin')
    created_at = db.Column(db.DateTime, default=datetime.now)

