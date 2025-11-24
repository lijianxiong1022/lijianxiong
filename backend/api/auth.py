from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from models import db, User, Admin
from utils import hash_password, verify_password, hash_pay_password, verify_pay_password
from api import api_bp

@api_bp.route('/user/register', methods=['POST'])
def user_register():
    """用户注册"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['name', 'phone', 'password', 'payPassword']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段: {field}',
                    'data': None
                }), 400
        
        name = data['name'].strip()
        phone = data['phone'].strip()
        password = data['password']
        pay_password = data['payPassword']
        promo_code = data.get('promoCode', '').strip()
        
        # 验证手机号格式
        if not phone.isdigit() or len(phone) != 11 or not phone.startswith('1'):
            return jsonify({
                'success': False,
                'message': '手机号格式不正确',
                'data': None
            }), 400
        
        # 验证支付密码格式
        if not pay_password.isdigit() or len(pay_password) != 6:
            return jsonify({
                'success': False,
                'message': '支付密码必须是6位数字',
                'data': None
            }), 400
        
        # 检查手机号是否已注册
        if User.query.filter_by(phone=phone).first():
            return jsonify({
                'success': False,
                'message': '该手机号已被注册',
                'data': None
            }), 400
        
        # 处理推广码（用于绑定上级关系）- 必填项
        if not promo_code:
            return jsonify({
                'success': False,
                'message': '推广码为必填项，必须有上级才可以注册',
                'data': None
            }), 400
        
        # 验证推广码格式
        if not promo_code.isdigit() or len(promo_code) != 6:
            return jsonify({
                'success': False,
                'message': '推广码必须是6位数字',
                'data': None
            }), 400
        
        # 检查推广码是否存在（如果是上级推广码）
        parent_user = User.query.filter_by(promo_code=promo_code).first()
        if not parent_user:
            return jsonify({
                'success': False,
                'message': '推广码不存在，无法绑定上级关系',
                'data': None
            }), 400
        parent_id = parent_user.id
        
        # 生成用户推广码
        user_promo_code = User.generate_promo_code()
        
        # 创建用户
        user = User(
            promo_code=user_promo_code,
            name=name,
            phone=phone,
            password=hash_password(password),
            pay_password=hash_pay_password(pay_password),
            parent_id=parent_id,
            user_type='ordinary'
        )
        
        db.session.add(user)
        db.session.commit()
        
        # 生成Token - identity必须是字符串，额外信息放在additional_claims中
        token = create_access_token(
            identity=str(user.id),
            additional_claims={'type': 'user', 'id': user.id}
        )
        
        return jsonify({
            'success': True,
            'message': '注册成功',
            'data': {
                'userId': user.id,
                'promoCode': user.promo_code,
                'token': token
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'注册失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/user/login', methods=['POST'])
def user_login():
    """用户登录"""
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        password = data.get('password', '')
        
        if not phone or not password:
            return jsonify({
                'success': False,
                'message': '手机号和密码不能为空',
                'data': None
            }), 400
        
        # 查找用户
        user = User.query.filter_by(phone=phone).first()
        if not user or not verify_password(user.password, password):
            return jsonify({
                'success': False,
                'message': '手机号或密码错误',
                'data': None
            }), 401
        
        # 生成Token - identity必须是字符串，额外信息放在additional_claims中
        token = create_access_token(
            identity=str(user.id),
            additional_claims={'type': 'user', 'id': user.id}
        )
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'data': {
                'token': token,
                'user': user.to_dict()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'登录失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/user/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    """获取用户信息"""
    try:
        from flask_jwt_extended import get_jwt
        identity_str = get_jwt_identity()  # 这是字符串形式的用户ID
        claims = get_jwt()  # 获取claims，包含additional_claims
        
        print(f'[DEBUG] get_user_profile - identity: {identity_str}, claims: {claims}')
        
        # 从claims中获取type，如果没有则从identity_str推断
        user_type = claims.get('type', 'user')
        user_id = claims.get('id') or int(identity_str)
        
        if user_type != 'user':
            print(f'[DEBUG] get_user_profile - 无效的Token类型: {user_type}')
            return jsonify({
                'success': False,
                'message': '无效的Token',
                'data': None
            }), 401
        
        user = User.query.get(user_id)
        if not user:
            print(f'[DEBUG] get_user_profile - 用户不存在: {user_id}')
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'data': None
            }), 404
        
        # 获取用户信息，包括上级信息和统计信息
        user_dict = user.to_dict()
        
        # 用户自己查看时，显示完整手机号（不隐藏）
        user_dict['phone'] = user.phone
        
        # 获取上级用户信息
        if user.parent_id:
            parent_user = User.query.get(user.parent_id)
            if parent_user:
                user_dict['parent'] = {
                    'name': parent_user.name,
                    'phone': parent_user.phone
                }
        
        # 计算现金收益（代理向下售卖的差价之和）
        # 现金收益 = 所有转账给下级的交易中，(转账单价 - 购买单价) * 转账数量
        # 使用FIFO逻辑，基于实际充值金额计算
        cash_profit = 0.0
        if user.user_type == 'agent':
            # 获取所有转出交易（transfer_out），按时间正序排列
            from models import Transaction
            
            transfer_out_transactions = Transaction.query.filter_by(
                user_id=user.id,
                transaction_type='transfer_out'
            ).order_by(Transaction.created_at.asc()).all()
            
            # 获取所有充值记录，按时间正序排列（FIFO）
            recharge_transactions = Transaction.query.filter_by(
                user_id=user.id,
                transaction_type='recharge'
            ).order_by(Transaction.created_at.asc()).all()
            
            # 构建充值记录队列（FIFO）
            recharge_queue = []
            for recharge in recharge_transactions:
                if recharge.actual_cash_amount and recharge.points_change:
                    points_amount = float(recharge.points_change)
                    actual_cash = float(recharge.actual_cash_amount)
                    actual_unit_price = actual_cash / points_amount if points_amount > 0 else 0
                    recharge_queue.append({
                        'remaining_points': points_amount,
                        'actual_unit_price': actual_unit_price
                    })
            
            # 计算每笔转账的收益（使用FIFO逻辑）
            for trans in transfer_out_transactions:
                if trans.related_user_id and trans.unit_price:
                    # 获取转账数量和单价
                    transfer_quantity = abs(float(trans.points_change))
                    transfer_unit_price = float(trans.unit_price)
                    
                    # 使用FIFO逻辑计算购买单价
                    remaining_transfer = transfer_quantity
                    total_cost = 0.0
                    
                    for recharge_item in recharge_queue:
                        if remaining_transfer <= 0:
                            break
                        
                        if recharge_item['remaining_points'] > 0:
                            # 从这笔充值中使用的金币数量
                            used_points = min(remaining_transfer, recharge_item['remaining_points'])
                            used_cost = used_points * recharge_item['actual_unit_price']
                            total_cost += used_cost
                            remaining_transfer -= used_points
                            recharge_item['remaining_points'] -= used_points
                    
                    # 如果还有剩余未分配的金币（理论上不应该发生），使用默认单价
                    if remaining_transfer > 0:
                        from utils import get_system_settings, calculate_agent_purchase_price
                        settings = get_system_settings()
                        exchange_rate = float(settings.get('coinExchangeRate', 10.0))
                        recharge_discount_rules = settings.get('rechargeDiscountRules', [])
                        default_unit_price = calculate_agent_purchase_price(
                            remaining_transfer,
                            exchange_rate,
                            recharge_discount_rules
                        )
                        total_cost += remaining_transfer * default_unit_price
                    
                    # 计算平均购买单价
                    average_purchase_unit_price = total_cost / transfer_quantity if transfer_quantity > 0 else 0
                    
                    # 计算收益：差价 * 数量
                    profit = (transfer_unit_price - average_purchase_unit_price) * transfer_quantity
                    cash_profit += profit
        
        user_dict['cashProfit'] = round(cash_profit, 2)
        
        print(f'[DEBUG] get_user_profile - 成功获取用户信息: {user.id}')
        return jsonify({
            'success': True,
            'data': user_dict
        })
        
    except Exception as e:
        print(f'[DEBUG] get_user_profile - 异常: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取用户信息失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/user/validate-promo-code', methods=['POST'])
def validate_promo_code():
    """验证推广码是否存在（用于绑定上级）"""
    try:
        data = request.get_json()
        promo_code = data.get('promoCode', '').strip()
        
        if not promo_code or not promo_code.isdigit() or len(promo_code) != 6:
            return jsonify({
                'success': False,
                'message': '推广码格式不正确',
                'data': {'isUnique': False}
            }), 400
        
        # 检查推广码是否存在（用于绑定上级，所以需要存在）
        user = User.query.filter_by(promo_code=promo_code).first()
        exists = user is not None
        
        return jsonify({
            'success': True,
            'data': {'isUnique': exists}  # isUnique 表示推广码存在（可以用来绑定上级）
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'验证失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/user/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    """修改登录密码"""
    try:
        identity_str = get_jwt_identity()
        claims = get_jwt()
        
        # 从claims中获取type和id
        user_type = claims.get('type', 'user')
        user_id = claims.get('id') or int(identity_str)
        
        if user_type != 'user':
            return jsonify({
                'success': False,
                'message': '无效的Token',
                'data': None
            }), 401
        
        data = request.get_json()
        old_password = data.get('oldPassword', '')
        new_password = data.get('newPassword', '')
        
        if not old_password or not new_password:
            return jsonify({
                'success': False,
                'message': '旧密码和新密码不能为空',
                'data': None
            }), 400
        
        if len(new_password) < 6:
            return jsonify({
                'success': False,
                'message': '新密码长度不能少于6位',
                'data': None
            }), 400
        
        # 获取当前用户
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'data': None
            }), 404
        
        # 验证旧密码
        if not verify_password(user.password, old_password):
            return jsonify({
                'success': False,
                'message': '旧密码错误',
                'data': None
            }), 400
        
        # 更新密码
        user.password = hash_password(new_password)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '修改登录密码成功',
            'data': None
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'修改登录密码失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/user/change-pay-password', methods=['PUT'])
@jwt_required()
def change_pay_password():
    """修改支付密码"""
    try:
        identity_str = get_jwt_identity()
        claims = get_jwt()
        
        # 从claims中获取type和id
        user_type = claims.get('type', 'user')
        user_id = claims.get('id') or int(identity_str)
        
        if user_type != 'user':
            return jsonify({
                'success': False,
                'message': '无效的Token',
                'data': None
            }), 401
        
        data = request.get_json()
        old_password = data.get('oldPassword', '')
        new_password = data.get('newPassword', '')
        
        if not old_password or not new_password:
            return jsonify({
                'success': False,
                'message': '旧密码和新密码不能为空',
                'data': None
            }), 400
        
        if not new_password.isdigit() or len(new_password) != 6:
            return jsonify({
                'success': False,
                'message': '支付密码必须是6位数字',
                'data': None
            }), 400
        
        # 获取当前用户
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'data': None
            }), 404
        
        # 验证旧密码
        if not verify_pay_password(user.pay_password, old_password):
            return jsonify({
                'success': False,
                'message': '旧支付密码错误',
                'data': None
            }), 400
        
        # 更新支付密码
        user.pay_password = hash_pay_password(new_password)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '修改支付密码成功',
            'data': None
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'修改支付密码失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/admin/login', methods=['POST'])
def admin_login():
    """管理员登录"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': '用户名和密码不能为空',
                'data': None
            }), 400
        
        # 查找管理员
        admin = Admin.query.filter_by(username=username).first()
        if not admin or not verify_password(admin.password, password):
            return jsonify({
                'success': False,
                'message': '用户名或密码错误',
                'data': None
            }), 401
        
        # 生成Token - identity必须是字符串，额外信息放在additional_claims中
        token = create_access_token(
            identity=str(admin.id),
            additional_claims={'type': 'admin', 'id': admin.id}
        )
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'data': {
                'token': token,
                'user': {
                    'id': admin.id,
                    'username': admin.username,
                    'name': admin.name,
                    'role': admin.role
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'登录失败: {str(e)}',
            'data': None
        }), 500

