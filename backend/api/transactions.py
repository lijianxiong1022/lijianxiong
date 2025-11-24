from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, date, timedelta
from models import db, User, Transaction
from api import api_bp

@api_bp.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    """获取交易记录列表"""
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
        
        # 获取查询参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 20))
        transaction_type = request.args.get('transactionType')  # recharge, order_deduction, transfer_out, transfer_in, reward
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        
        # 构建查询
        query = Transaction.query.filter_by(user_id=user_id)
        
        if transaction_type:
            query = query.filter_by(transaction_type=transaction_type)
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(Transaction.created_at >= datetime.combine(start_date_obj, datetime.min.time()))
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(Transaction.created_at <= datetime.combine(end_date_obj, datetime.max.time()))
            except ValueError:
                pass
        
        # 分页
        pagination = query.order_by(Transaction.created_at.desc()).paginate(
            page=page, per_page=page_size, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'list': [t.to_dict() for t in pagination.items],
                'total': pagination.total,
                'page': page,
                'pageSize': page_size
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取交易记录失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/transactions/cash-profit', methods=['GET'])
@jwt_required()
def get_cash_profit_list():
    """获取现金收益清单（代理用户）"""
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
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'data': None
            }), 404
        
        if user.user_type != 'agent':
            return jsonify({
                'success': False,
                'message': '只有代理用户才能查看现金收益',
                'data': None
            }), 403
        
        # 获取所有转出交易（transfer_out），按时间正序排列（最早的在前面）
        transfer_out_transactions = Transaction.query.filter_by(
            user_id=user.id,
            transaction_type='transfer_out'
        ).order_by(Transaction.created_at.asc()).all()
        
        # 获取所有充值记录（recharge），按时间正序排列（最早的在前面），用于FIFO计算
        recharge_transactions = Transaction.query.filter_by(
            user_id=user.id,
            transaction_type='recharge'
        ).order_by(Transaction.created_at.asc()).all()
        
        # 构建充值记录队列（FIFO）
        # 每个充值记录包含：剩余金币数量、实际单价
        recharge_queue = []
        for recharge in recharge_transactions:
            if recharge.actual_cash_amount and recharge.points_change:
                points_amount = float(recharge.points_change)
                actual_cash = float(recharge.actual_cash_amount)
                actual_unit_price = actual_cash / points_amount if points_amount > 0 else 0
                recharge_queue.append({
                    'id': recharge.id,
                    'points_amount': points_amount,
                    'remaining_points': points_amount,  # 剩余可用金币
                    'actual_cash': actual_cash,
                    'actual_unit_price': actual_unit_price,
                    'created_at': recharge.created_at
                })
        
        # 计算每笔转账的收益（使用FIFO逻辑）
        profit_list = []
        total_profit = 0.0
        
        for trans in transfer_out_transactions:
            if trans.related_user_id and trans.unit_price:
                # 获取转账数量和单价
                transfer_quantity = abs(float(trans.points_change))
                transfer_unit_price = float(trans.unit_price)
                
                # 使用FIFO逻辑计算购买单价
                # 从最早的充值记录中扣除金币，直到满足转账数量
                remaining_transfer = transfer_quantity
                total_cost = 0.0
                purchase_details = []  # 记录使用的充值记录详情
                
                print(f'[DEBUG] 现金收益计算: 转账ID={trans.id}, 转账数量={transfer_quantity}, 转账单价={transfer_unit_price}')
                print(f'[DEBUG] 充值队列初始状态: {[(r["id"], r["remaining_points"], r["actual_unit_price"]) for r in recharge_queue]}')
                
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
                        
                        print(f'[DEBUG] 使用充值记录 ID={recharge_item["id"]}: 使用{used_points}金币, 单价={recharge_item["actual_unit_price"]:.2f}, 成本={used_cost:.2f}, 剩余={recharge_item["remaining_points"]:.2f}')
                        
                        purchase_details.append({
                            'quantity': used_points,
                            'unit_price': recharge_item['actual_unit_price'],
                            'recharge_id': recharge_item['id']
                        })
                
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
                    print(f'[DEBUG] 使用默认单价: 剩余{remaining_transfer}金币, 单价={default_unit_price:.2f}')
                    purchase_details.append({
                        'quantity': remaining_transfer,
                        'unit_price': default_unit_price,
                        'recharge_id': None
                    })
                
                # 获取收款人信息
                to_user = User.query.get(trans.related_user_id)
                receiver_name = to_user.name if to_user else '--'
                
                # 计算总收益：分别计算每个购买详情的收益
                total_profit_for_transfer = 0.0
                for detail in purchase_details:
                    detail_quantity = detail['quantity']
                    detail_purchase_price = detail['unit_price']
                    detail_profit = (transfer_unit_price - detail_purchase_price) * detail_quantity
                    total_profit_for_transfer += detail_profit
                
                total_profit += total_profit_for_transfer
                
                # 判断是否使用了多个不同单价
                unique_prices = set([detail['unit_price'] for detail in purchase_details])
                is_multi_price = len(unique_prices) > 1
                
                # 计算平均购买单价（用于单单价显示）
                average_purchase_unit_price = total_cost / transfer_quantity if transfer_quantity > 0 else 0
                
                print(f'[DEBUG] 计算结果: 总成本={total_cost:.2f}, 平均单价={average_purchase_unit_price:.2f}, 总收益={total_profit_for_transfer:.2f}, 是否多单价={is_multi_price}')
                
                profit_list.append({
                    'id': trans.id,
                    'createdAt': trans.created_at.strftime('%Y-%m-%d %H:%M:%S') if trans.created_at else None,
                    'receiverName': receiver_name,
                    'quantity': transfer_quantity,
                    'transferUnitPrice': transfer_unit_price,
                    'purchaseUnitPrice': round(average_purchase_unit_price, 2),  # 平均单价（用于单单价显示）
                    'purchaseDetails': purchase_details,  # 所有使用的充值记录详情
                    'profit': round(total_profit_for_transfer, 2),
                    'isMultiPrice': is_multi_price  # 是否使用了多个不同单价
                })
        
        # 按时间倒序排列（最新的在前面）
        profit_list.reverse()
        
        return jsonify({
            'success': True,
            'data': {
                'list': profit_list,
                'totalProfit': round(total_profit, 2)
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取现金收益清单失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/transactions/statistics', methods=['GET'])
@jwt_required()
def get_transaction_statistics():
    """获取交易统计信息"""
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
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        first_day_of_month = date(today.year, today.month, 1)
        first_day_of_last_month = (first_day_of_month - timedelta(days=1)).replace(day=1)
        last_day_of_last_month = first_day_of_month - timedelta(days=1)
        
        # 今日统计
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        today_recharge = db.session.query(db.func.sum(Transaction.points_change)).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == 'recharge',
            Transaction.created_at >= today_start,
            Transaction.created_at <= today_end
        ).scalar() or 0
        
        today_order_deduction = db.session.query(db.func.sum(db.func.abs(Transaction.points_change))).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == 'order_deduction',
            Transaction.created_at >= today_start,
            Transaction.created_at <= today_end
        ).scalar() or 0
        
        # 本月统计
        month_start = datetime.combine(first_day_of_month, datetime.min.time())
        month_end = datetime.combine(today, datetime.max.time())
        
        month_recharge = db.session.query(db.func.sum(Transaction.points_change)).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == 'recharge',
            Transaction.created_at >= month_start,
            Transaction.created_at <= month_end
        ).scalar() or 0
        
        month_order_deduction = db.session.query(db.func.sum(db.func.abs(Transaction.points_change))).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == 'order_deduction',
            Transaction.created_at >= month_start,
            Transaction.created_at <= month_end
        ).scalar() or 0
        
        # 上月统计
        last_month_start = datetime.combine(first_day_of_last_month, datetime.min.time())
        last_month_end = datetime.combine(last_day_of_last_month, datetime.max.time())
        
        last_month_order_deduction = db.session.query(db.func.sum(db.func.abs(Transaction.points_change))).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == 'order_deduction',
            Transaction.created_at >= last_month_start,
            Transaction.created_at <= last_month_end
        ).scalar() or 0
        
        # 昨日统计
        yesterday_start = datetime.combine(yesterday, datetime.min.time())
        yesterday_end = datetime.combine(yesterday, datetime.max.time())
        
        yesterday_order_deduction = db.session.query(db.func.sum(db.func.abs(Transaction.points_change))).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == 'order_deduction',
            Transaction.created_at >= yesterday_start,
            Transaction.created_at <= yesterday_end
        ).scalar() or 0
        
        return jsonify({
            'success': True,
            'data': {
                'today': {
                    'recharge': float(today_recharge),
                    'orderDeduction': float(today_order_deduction)
                },
                'yesterday': {
                    'orderDeduction': float(yesterday_order_deduction)
                },
                'month': {
                    'recharge': float(month_recharge),
                    'orderDeduction': float(month_order_deduction)
                },
                'lastMonth': {
                    'orderDeduction': float(last_month_order_deduction)
                }
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取交易统计失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/rewards', methods=['GET'])
@jwt_required()
def get_rewards():
    """获取奖励记录列表"""
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
        
        # 获取查询参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 20))
        reward_type = request.args.get('rewardType')  # direct, indirect
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        
        # 构建查询（只查询奖励类型的交易）
        query = Transaction.query.filter_by(
            user_id=user_id,
            transaction_type='reward'
        )
        
        if reward_type:
            # 根据描述判断是直推还是间推
            if reward_type == 'direct':
                query = query.filter(Transaction.description.like('%直推%'))
            elif reward_type == 'indirect':
                query = query.filter(Transaction.description.like('%间推%'))
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(Transaction.created_at >= datetime.combine(start_date_obj, datetime.min.time()))
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(Transaction.created_at <= datetime.combine(end_date_obj, datetime.max.time()))
            except ValueError:
                pass
        
        # 分页
        pagination = query.order_by(Transaction.created_at.desc()).paginate(
            page=page, per_page=page_size, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'list': [t.to_dict() for t in pagination.items],
                'total': pagination.total,
                'page': page,
                'pageSize': page_size
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取奖励记录失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/rewards/statistics', methods=['GET'])
@jwt_required()
def get_reward_statistics():
    """获取奖励统计信息"""
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
        
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # 今日直推奖励
        today_direct_reward = db.session.query(db.func.sum(Transaction.points_change)).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == 'reward',
            Transaction.description.like('%直推%'),
            Transaction.created_at >= today_start,
            Transaction.created_at <= today_end
        ).scalar() or 0
        
        # 今日间推奖励
        today_indirect_reward = db.session.query(db.func.sum(Transaction.points_change)).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == 'reward',
            Transaction.description.like('%间推%'),
            Transaction.created_at >= today_start,
            Transaction.created_at <= today_end
        ).scalar() or 0
        
        # 总直推奖励
        total_direct_reward = db.session.query(db.func.sum(Transaction.points_change)).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == 'reward',
            Transaction.description.like('%直推%')
        ).scalar() or 0
        
        # 总间推奖励
        total_indirect_reward = db.session.query(db.func.sum(Transaction.points_change)).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == 'reward',
            Transaction.description.like('%间推%')
        ).scalar() or 0
        
        return jsonify({
            'success': True,
            'data': {
                'today': {
                    'directReward': float(today_direct_reward),
                    'indirectReward': float(today_indirect_reward)
                },
                'total': {
                    'directReward': float(total_direct_reward),
                    'indirectReward': float(total_indirect_reward)
                }
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取奖励统计失败: {str(e)}',
            'data': None
        }), 500

