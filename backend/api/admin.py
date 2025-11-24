from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import db, User, Admin, Transaction
from utils import hash_pay_password, verify_password, create_transaction
from api import api_bp

# 注意：verify_password 在 utils.py 中已定义

@api_bp.route('/admin/users/<int:user_id>/pay-password', methods=['PUT'])
@jwt_required()
def update_user_pay_password(user_id):
    """管理员修改用户支付密码"""
    try:
        identity_str = get_jwt_identity()
        claims = get_jwt()
        
        # 从claims中获取type和id
        admin_type = claims.get('type', '')
        admin_id = claims.get('id') or (int(identity_str) if identity_str.isdigit() else None)
        
        # 验证是否为管理员
        if admin_type != 'admin':
            return jsonify({
                'success': False,
                'message': '需要管理员权限',
                'data': None
            }), 403
        
        # 验证管理员是否存在
        admin = Admin.query.get(admin_id)
        if not admin:
            return jsonify({
                'success': False,
                'message': '管理员不存在',
                'data': None
            }), 404
        
        data = request.get_json()
        new_pay_password = data.get('payPassword', '').strip()
        
        # 验证支付密码格式
        if not new_pay_password or not new_pay_password.isdigit() or len(new_pay_password) != 6:
            return jsonify({
                'success': False,
                'message': '支付密码必须是6位数字',
                'data': None
            }), 400
        
        # 获取目标用户
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'data': None
            }), 404
        
        # 更新支付密码
        user.pay_password = hash_pay_password(new_pay_password)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '支付密码修改成功',
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

@api_bp.route('/admin/recharge', methods=['POST'])
@jwt_required()
def recharge_user():
    """管理员为用户充值金币"""
    try:
        identity_str = get_jwt_identity()
        claims = get_jwt()
        
        # 从claims中获取type和id
        admin_type = claims.get('type', '')
        admin_id = claims.get('id') or (int(identity_str) if identity_str.isdigit() else None)
        
        # 验证是否为管理员
        if admin_type != 'admin':
            return jsonify({
                'success': False,
                'message': '需要管理员权限',
                'data': None
            }), 403
        
        # 验证管理员是否存在
        admin = Admin.query.get(admin_id)
        if not admin:
            return jsonify({
                'success': False,
                'message': '管理员不存在',
                'data': None
            }), 404
        
        data = request.get_json()
        promo_code = data.get('promoCode', '').strip()  # 支持通过推广码充值
        user_id = data.get('userId')
        points = data.get('points', 0)
        admin_password = data.get('adminPassword', '')
        
        # 验证必填字段
        if not promo_code and not user_id:
            return jsonify({
                'success': False,
                'message': '用户推广码或用户ID不能为空',
                'data': None
            }), 400
        
        if not points or points <= 0:
            return jsonify({
                'success': False,
                'message': '充值金额必须大于0',
                'data': None
            }), 400
        
        if not admin_password:
            return jsonify({
                'success': False,
                'message': '请输入管理员密码',
                'data': None
            }), 400
        
        # 验证管理员密码
        from utils import verify_password
        if not verify_password(admin.password, admin_password):
            return jsonify({
                'success': False,
                'message': '管理员密码错误',
                'data': None
            }), 400
        
        # 获取目标用户（优先使用推广码）
        if promo_code:
            user = User.query.filter_by(promo_code=promo_code).first()
        else:
            user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'data': None
            }), 404
        
        user_id = user.id  # 使用实际的用户ID
        
        # 计算实际需要支付的现金金额（考虑优惠）
        from utils import get_system_settings, calculate_recharge_price
        settings = get_system_settings()
        exchange_rate = float(settings.get('coinExchangeRate', 10.0))
        recharge_discount_rules = settings.get('rechargeDiscountRules', [])
        
        # 确保recharge_discount_rules是列表格式
        if not isinstance(recharge_discount_rules, list):
            recharge_discount_rules = []
        
        # 调试日志
        print(f'[DEBUG] 充值计算: points={points}, exchange_rate={exchange_rate}, discount_rules={recharge_discount_rules}')
        print(f'[DEBUG] 完整settings: {settings}')
        
        # 计算实际支付的现金金额
        actual_cash_amount = calculate_recharge_price(points, exchange_rate, recharge_discount_rules)
        
        # 调试日志
        print(f'[DEBUG] 充值结果: actual_cash_amount={actual_cash_amount}, unit_price={actual_cash_amount/points if points > 0 else 0:.2f}')
        
        # 执行充值
        current_points = float(user.points) if user.points is not None else 0.0
        user.points = current_points + points
        
        # 创建交易记录（记录实际支付的现金金额）
        create_transaction(
            user_id=user_id,
            transaction_type='recharge',
            points_change=points,
            balance=float(user.points),
            description=f'管理员 {admin.name} 充值',
            actual_cash_amount=actual_cash_amount
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '充值成功',
            'data': {
                'points': float(user.points),
                'rechargeAmount': points
            }
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'充值失败: {str(e)}',
            'data': None
        }), 500

