from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
from models import db, User, Transaction
from utils import verify_pay_password, get_system_settings, create_transaction, calculate_agent_purchase_price
from api import api_bp

@api_bp.route('/points/transfer', methods=['POST'])
@jwt_required()
def transfer_points():
    """金币转账"""
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
        to_phone = data.get('toPhone', '').strip()
        quantity = data.get('quantity', 0)
        unit_price = data.get('unitPrice', 0)
        pay_password = data.get('payPassword', '')
        confirmed_low_price = data.get('confirmedLowPrice', False)  # 是否确认低于购买价转账
        
        # 验证必填字段
        if not to_phone:
            return jsonify({
                'success': False,
                'message': '请输入收款人手机号',
                'data': None
            }), 400
        
        if not quantity or quantity <= 0:
            return jsonify({
                'success': False,
                'message': '转账数量必须大于0',
                'data': None
            }), 400
        
        if not unit_price or unit_price <= 0:
            return jsonify({
                'success': False,
                'message': '转账单价必须大于0',
                'data': None
            }), 400
        
        if not pay_password:
            return jsonify({
                'success': False,
                'message': '请输入支付密码',
                'data': None
            }), 400
        
        # 验证手机号格式
        if not to_phone.isdigit() or len(to_phone) != 11 or not to_phone.startswith('1'):
            return jsonify({
                'success': False,
                'message': '收款人手机号格式不正确',
                'data': None
            }), 400
        
        # 获取系统设置
        settings = get_system_settings()
        transfer_limits = settings.get('transferLimits', {})
        min_quantity = float(transfer_limits.get('minQuantity', 10))
        max_unit_price = float(transfer_limits.get('maxUnitPrice', 1.5))
        exchange_rate = float(settings.get('coinExchangeRate', 10.0))  # 默认10元=1金币
        recharge_discount_rules = settings.get('rechargeDiscountRules', [])
        
        # 调试日志
        print(f'[DEBUG] 转账限制配置: minQuantity={min_quantity}, maxUnitPrice={max_unit_price}, exchangeRate={exchange_rate}')
        print(f'[DEBUG] 转账请求: quantity={quantity}, unit_price={unit_price}')
        
        # 验证转账限制
        if quantity < min_quantity:
            return jsonify({
                'success': False,
                'message': f'转账数量不能低于 {min_quantity}',
                'data': None
            }), 400
        
        if unit_price > max_unit_price:
            return jsonify({
                'success': False,
                'message': f'转账单价不能高于 {max_unit_price} 元/金币',
                'data': None
            }), 400
        
        # 获取当前用户
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'data': None
            }), 404
        
        # 获取当前金币余额
        current_points = float(user.points) if user.points is not None else 0.0
        
        # 使用FIFO逻辑计算最低购买单价（基于实际充值记录）
        # 获取所有充值记录，按时间正序排列（FIFO）
        from models import Transaction
        recharge_transactions = Transaction.query.filter_by(
            user_id=user_id,
            transaction_type='recharge'
        ).order_by(Transaction.created_at.asc()).all()
        
        # 获取所有之前的转账记录（transfer_out），用于计算已使用的金币
        previous_transfers = Transaction.query.filter_by(
            user_id=user_id,
            transaction_type='transfer_out'
        ).order_by(Transaction.created_at.asc()).all()
        
        # 构建充值记录队列（FIFO），并计算每笔充值已使用的金币
        recharge_queue = []
        for recharge in recharge_transactions:
            if recharge.actual_cash_amount and recharge.points_change:
                points_amount = float(recharge.points_change)
                actual_cash = float(recharge.actual_cash_amount)
                actual_unit_price = actual_cash / points_amount if points_amount > 0 else 0
                recharge_queue.append({
                    'recharge_id': recharge.id,
                    'total_points': points_amount,
                    'remaining_points': points_amount,  # 初始化为总金额，后续会扣除已使用的部分
                    'actual_unit_price': actual_unit_price
                })
        
        # 按照FIFO顺序，从充值记录中扣除已转账的部分
        remaining_previous_transfers = sum([abs(float(t.points_change)) for t in previous_transfers])
        for recharge_item in recharge_queue:
            if remaining_previous_transfers <= 0:
                break
            
            if recharge_item['remaining_points'] > 0:
                # 从这笔充值中已使用的金币数量
                used_by_previous = min(remaining_previous_transfers, recharge_item['remaining_points'])
                recharge_item['remaining_points'] -= used_by_previous
                remaining_previous_transfers -= used_by_previous
        
        # 计算当前转账数量对应的购买单价（使用FIFO）
        remaining_transfer = quantity
        total_cost = 0.0
        min_unit_price = None
        
        for recharge_item in recharge_queue:
            if remaining_transfer <= 0:
                break
            
            if recharge_item['remaining_points'] > 0:
                # 从这笔充值中使用的金币数量
                used_points = min(remaining_transfer, recharge_item['remaining_points'])
                used_cost = used_points * recharge_item['actual_unit_price']
                total_cost += used_cost
                remaining_transfer -= used_points
                
                # 记录最低单价
                if min_unit_price is None or recharge_item['actual_unit_price'] < min_unit_price:
                    min_unit_price = recharge_item['actual_unit_price']
        
        # 如果还有剩余未分配的金币，使用理论计算
        if remaining_transfer > 0:
            theoretical_unit_price = calculate_agent_purchase_price(
                remaining_transfer,
                exchange_rate,
                recharge_discount_rules
            )
            total_cost += remaining_transfer * theoretical_unit_price
            if min_unit_price is None or theoretical_unit_price < min_unit_price:
                min_unit_price = theoretical_unit_price
        
        # 计算平均购买单价
        purchase_unit_price = total_cost / quantity if quantity > 0 else (min_unit_price or exchange_rate)
        
        # 调试日志
        print(f'[DEBUG] 转账FIFO计算: quantity={quantity}, purchase_unit_price={purchase_unit_price:.2f}, total_cost={total_cost:.2f}')
        print(f'[DEBUG] 充值记录队列: {[(r["recharge_id"], r["remaining_points"], r["actual_unit_price"]) for r in recharge_queue]}')
        
        # 验证价格下限：转账单价不能低于购买单价
        if unit_price < purchase_unit_price:
            if not confirmed_low_price:
                return jsonify({
                    'success': False,
                    'message': f'转账单价不能低于您的购买单价 {purchase_unit_price} 元/金币，是否确认继续？',
                    'data': {
                        'purchaseUnitPrice': purchase_unit_price,
                        'needConfirm': True
                    }
                }), 400
            # 用户已确认，允许继续
        
        # 验证支付密码
        if not verify_pay_password(user.pay_password, pay_password):
            return jsonify({
                'success': False,
                'message': '支付密码错误',
                'data': None
            }), 400
        
        # 计算转账金额（注意：这里total_points是金币数量，不是现金）
        total_points = quantity  # 转账的金币数量
        
        # 验证余额（使用之前获取的current_points）
        if current_points < total_points:
            return jsonify({
                'success': False,
                'message': f'金币不足，当前余额: {current_points:.2f}, 需要: {total_points:.2f}',
                'data': None
            }), 400
        
        # 获取收款人
        to_user = User.query.filter_by(phone=to_phone).first()
        if not to_user:
            return jsonify({
                'success': False,
                'message': '收款人不存在',
                'data': None
            }), 404
        
        if to_user.id == user_id:
            return jsonify({
                'success': False,
                'message': '不能转账给自己',
                'data': None
            }), 400
        
        # 执行转账
        # 扣除转出方金币
        user.points = current_points - total_points
        to_user_balance_before = float(to_user.points) if to_user.points is not None else 0.0
        to_user.points = to_user_balance_before + total_points
        
        # 创建交易记录（保存转账单价）
        create_transaction(
            user_id=user_id,
            transaction_type='transfer_out',
            points_change=-total_points,
            balance=float(user.points),
            description=f'转账给 {to_user.name}({to_phone})，单价：{unit_price}元/金币',
            related_user_id=to_user.id,
            unit_price=unit_price  # 保存转账单价
        )
        
        create_transaction(
            user_id=to_user.id,
            transaction_type='transfer_in',
            points_change=total_points,
            balance=float(to_user.points),
            description=f'{user.name}({user.phone}) 转账收入',
            related_user_id=user_id
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '转账成功',
            'data': {
                'points': float(user.points),
                'toUserName': to_user.name
            }
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'转账失败: {str(e)}',
            'data': None
        }), 500

