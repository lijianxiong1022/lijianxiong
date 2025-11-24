from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, date
from sqlalchemy import or_
import math
from models import db, User, Order, NonMember, Transaction, ExceptionOrder
from utils import get_base_price, get_discount_by_order_count, calculate_order_price, get_system_settings, create_transaction
from api import api_bp

@api_bp.route('/orders', methods=['POST'])
@jwt_required()
def create_order():
    """创建报单"""
    try:
        identity_str = get_jwt_identity()  # 这是字符串形式的用户ID
        claims = get_jwt()  # 获取claims，包含additional_claims
        
        # 从claims中获取type和id
        user_type = claims.get('type', 'user')
        user_id = claims.get('id') or int(identity_str)
        
        if user_type != 'user':
            return jsonify({
                'success': False,
                'message': '无效的Token',
                'data': None
            }), 401
        # 重新从数据库获取用户，确保获取最新的金币余额
        # 使用session.query().filter_by()确保获取最新数据
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'data': None
            }), 404
        
        # 确保points是数值类型
        current_points = float(user.points) if user.points is not None else 0.0
        print(f'[DEBUG] create_order - 用户ID: {user_id}, 当前金币余额: {current_points}')
        
        data = request.get_json()
        non_member_ids = data.get('nonMemberIds', [])
        settlement_date_str = data.get('settlementDate', '')
        quantity = data.get('quantity', 0)
        
        # 验证必填字段
        if not non_member_ids or not settlement_date_str or not quantity:
            return jsonify({
                'success': False,
                'message': '缺少必填字段',
                'data': None
            }), 400
        
        # 验证日期格式和不能选择今天之前的日期
        try:
            settlement_date = datetime.strptime(settlement_date_str, '%Y-%m-%d').date()
            today = date.today()
            if settlement_date < today:
                return jsonify({
                    'success': False,
                    'message': '不能选择今天之前的日期',
                    'data': None
                }), 400
        except ValueError:
            return jsonify({
                'success': False,
                'message': '日期格式不正确',
                'data': None
            }), 400
        
        # 验证非会员用户是否存在且属于当前用户
        non_members = []
        for nm_id in non_member_ids:
            non_member = NonMember.query.filter_by(id=nm_id, owner_id=user_id).first()
            if not non_member:
                return jsonify({
                    'success': False,
                    'message': f'非会员用户ID {nm_id} 不存在或不属于当前用户',
                    'data': None
                }), 400
            non_members.append(non_member)
        
        # 获取系统配置
        settings = get_system_settings()
        
        # 计算基础单价（传入settings避免重复查询）
        base_price = get_base_price(settlement_date, settings)
        
        # 只按照单次报单数量进行优惠，不累计当日订单数
        # 获取折扣率（直接使用本次报单数量，不累计当日已有订单）
        discount_rules = settings.get('discountRules', [])
        print(f'[DEBUG] create_order - 报单日期: {settlement_date}, 本次数量: {quantity}')
        print(f'[DEBUG] create_order - 折扣规则配置: {discount_rules}')
        discount_rate = get_discount_by_order_count(quantity, discount_rules)
        print(f'[DEBUG] create_order - 最终折扣率: {discount_rate} (匹配规则: minOrders={[r["minOrders"] for r in discount_rules if quantity >= r["minOrders"]]})')
        
        # 计算总价：数量 * 单价 * 折扣率
        final_price, total_points = calculate_order_price(base_price, discount_rate, quantity)
        
        print(f'[DEBUG] create_order - 基础单价: {base_price}, 折扣率: {discount_rate}, 数量: {quantity}')
        print(f'[DEBUG] create_order - 折扣后单价: {final_price}, 总金币: {total_points}')
        print(f'[DEBUG] create_order - 计算过程: 数量({quantity}) * 单价({base_price}) * 折扣率({discount_rate}) = {quantity} * {base_price} * {discount_rate} = {total_points}')
        
        # 检查金币余额（使用之前获取的current_points）
        # 使用round确保比较时精度一致
        if round(current_points, 2) < round(total_points, 2):
            return jsonify({
                'success': False,
                'message': f'金币不足，当前余额: {current_points:.2f}, 需要: {total_points:.2f}',
                'data': None
            }), 400
        
        # 创建订单
        orders = []
        for non_member in non_members:
            order = Order(
                user_id=user_id,
                non_member_id=non_member.id,
                settlement_date=settlement_date,
                base_price=base_price,
                discount_rate=discount_rate,
                final_price=final_price / quantity,  # 单个订单的单价
                quantity=1,
                total_points=total_points / quantity,  # 单个订单的金币
                status='pending'
            )
            db.session.add(order)
            orders.append(order)
        
        # 扣除用户金币（使用之前获取的current_points）
        user.points = current_points - total_points
        
        # 创建交易记录（使用更新后的余额）
        # final_price 是折扣后的单价，需要显示基础单价和折扣后的单价
        create_transaction(
            user_id=user_id,
            transaction_type='order_deduction',
            points_change=-total_points,
            balance=float(user.points),
            description=f'报单扣除，日期: {settlement_date_str}, 数量: {quantity}, 基础单价: {base_price:.2f}, 折扣后单价: {final_price:.2f}, 折扣率: {discount_rate*100:.1f}%'
        )
        
        # 计算并发放奖励（如果有上级，排除平台用户888888）
        if user.parent_id:
            parent = User.query.get(user.parent_id)
            # 排除平台用户（推广码888888）
            if parent and parent.user_type == 'agent' and parent.promo_code != '888888':
                # 直推奖励（保留小数，不四舍五入，直接截断）
                direct_reward = total_points * settings.get('rewardRates', {}).get('direct', 0.03)
                # 保留4位小数，向下截断（不四舍五入）
                direct_reward = math.floor(direct_reward * 10000) / 10000
                parent.points = float(parent.points) + direct_reward
                
                create_transaction(
                    user_id=parent.id,
                    transaction_type='reward',
                    points_change=direct_reward,
                    balance=float(parent.points),
                    description=f'直推下级 {user.name} 报单奖励'
                )
                
                # 间推奖励（下下级）
                if parent.parent_id:
                    grandparent = User.query.get(parent.parent_id)
                    # 排除平台用户（推广码888888）
                    if grandparent and grandparent.user_type == 'agent' and grandparent.promo_code != '888888':
                        indirect_reward = total_points * settings.get('rewardRates', {}).get('indirect', 0.01)
                        # 保留4位小数，向下截断（不四舍五入）
                        indirect_reward = math.floor(indirect_reward * 10000) / 10000
                        grandparent.points = float(grandparent.points) + indirect_reward
                        
                        create_transaction(
                            user_id=grandparent.id,
                            transaction_type='reward',
                            points_change=indirect_reward,
                            balance=float(grandparent.points),
                            description=f'间推下级 {user.name} 报单奖励'
                        )
        
        db.session.commit()
        
        # 刷新用户对象，获取最新的金币余额
        db.session.refresh(user)
        remaining_points = float(user.points) if user.points is not None else 0.0
        
        print(f'[DEBUG] create_order - 报单成功，剩余金币: {remaining_points}')
        
        return jsonify({
            'success': True,
            'message': '报单成功',
            'data': {
                'orderIds': [order.id for order in orders],
                'totalPoints': total_points,
                'remainingPoints': remaining_points,
                'basePrice': base_price,
                'discountRate': discount_rate,
                'finalPrice': final_price
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'报单失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    """获取订单列表（按提交时间分组汇总）"""
    try:
        identity_str = get_jwt_identity()  # 这是字符串形式的用户ID
        claims = get_jwt()  # 获取claims，包含additional_claims
        
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
        query_date = request.args.get('queryDate')  # 查询日期（按提交时间）
        settlement_date = request.args.get('settlementDate')  # 报单日期筛选
        status_filter = request.args.get('status')  # 状态筛选
        keyword = request.args.get('keyword', '').strip()  # 关键词搜索
        
        # 构建查询
        query = Order.query.filter_by(user_id=user_id)
        
        # 状态筛选（需要在关键词搜索之前处理，避免join冲突）
        if status_filter:
            if status_filter == 'exception_pending':
                # 异常待审核：有异常订单且异常订单状态为pending
                query = query.join(ExceptionOrder, Order.id == ExceptionOrder.order_id).filter(ExceptionOrder.status == 'pending')
            elif status_filter == 'exception_approved':
                # 异常已受理：有异常订单且异常订单状态为exported
                query = query.join(ExceptionOrder, Order.id == ExceptionOrder.order_id).filter(ExceptionOrder.status == 'exported')
            elif status_filter == 'pending':
                # 待审核：订单状态为pending且没有异常订单
                query = query.filter(
                    Order.status == 'pending',
                    ~Order.id.in_(db.session.query(ExceptionOrder.order_id))
                )
            elif status_filter == 'approved':
                # 已通过：订单状态为approved或exported为True，且没有异常订单
                query = query.filter(
                    ((Order.status == 'approved') | (Order.exported == True)),
                    ~Order.id.in_(db.session.query(ExceptionOrder.order_id))
                )
        
        # 关键词搜索（推广码、姓名、碰碰链接）- 使用子查询避免join冲突
        if keyword:
            # 先找到匹配的用户ID和非会员ID
            matching_user_ids = db.session.query(User.id).filter(
                or_(
                    User.promo_code.like(f'%{keyword}%'),
                    User.name.like(f'%{keyword}%')
                )
            ).subquery()
            
            matching_nonmember_ids = db.session.query(NonMember.id).filter(
                or_(
                    NonMember.name.like(f'%{keyword}%'),
                    NonMember.link.like(f'%{keyword}%')
                )
            ).subquery()
            
            # 过滤订单：用户匹配或非会员匹配
            query = query.filter(
                or_(
                    Order.user_id.in_(db.session.query(matching_user_ids.c.id)),
                    Order.non_member_id.in_(db.session.query(matching_nonmember_ids.c.id))
                )
            )
        
        if query_date:
            # 查询指定日期的订单（按created_at的日期部分）
            date_obj = datetime.strptime(query_date, '%Y-%m-%d').date()
            start_datetime = datetime.combine(date_obj, datetime.min.time())
            end_datetime = datetime.combine(date_obj, datetime.max.time())
            query = query.filter(
                Order.created_at >= start_datetime,
                Order.created_at <= end_datetime
            )
        
        if settlement_date:
            # 按报单日期筛选
            settlement_date_obj = datetime.strptime(settlement_date, '%Y-%m-%d').date()
            query = query.filter(Order.settlement_date == settlement_date_obj)
        
        # 获取所有订单
        all_orders = query.order_by(Order.created_at.desc()).all()
        
        # 按created_at分组（精确到秒，同一秒内的订单视为一次报单）
        from collections import defaultdict
        grouped_orders = defaultdict(list)
        
        for order in all_orders:
            # 使用created_at作为分组键（精确到秒）
            group_key = order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            grouped_orders[group_key].append(order)
        
        # 构建汇总列表
        summary_list = []
        total_quantity = 0
        total_points = 0
        submission_count = 0
        
        for group_key, orders in sorted(grouped_orders.items(), reverse=True):
            # 计算本次报单的汇总
            group_quantity = sum(order.quantity for order in orders)
            group_points = sum(float(order.total_points) for order in orders)
            group_created_at = orders[0].created_at
            group_settlement_date = orders[0].settlement_date
            
            # 计算平均优惠单价（总金币 / 总数量）
            avg_discount_price = round(group_points / group_quantity, 2) if group_quantity > 0 else 0
            
            # 获取本次报单的所有订单详情（包含异常订单信息）
            order_details = []
            for order in orders:
                order_dict = order.to_dict()
                # 如果有异常订单，添加异常订单信息
                if order.exception_order:
                    order_dict['exceptionOrder'] = order.exception_order.to_dict()
                order_details.append(order_dict)
            
            summary_list.append({
                'submissionTime': group_created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'settlementDate': group_settlement_date.strftime('%Y-%m-%d') if group_settlement_date else None,
                'settlementDateShort': group_settlement_date.strftime('%m/%d') if group_settlement_date else None,  # 月/日格式
                'quantity': group_quantity,
                'totalPoints': round(group_points, 2),
                'avgDiscountPrice': avg_discount_price,  # 金币优惠单价
                'orderCount': len(orders),
                'orders': order_details
            })
            
            # 累计当日统计（有日期筛选时统计）
            if query_date or settlement_date:
                submission_count += 1
                total_quantity += group_quantity
                total_points += group_points
        
        return jsonify({
            'success': True,
            'data': {
                'list': summary_list,
                'total': len(summary_list),
                'statistics': {
                    'submissionCount': submission_count,
                    'totalQuantity': total_quantity,
                    'totalPoints': round(total_points, 2)
                } if (query_date or settlement_date) else None
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取订单列表失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/points/balance', methods=['GET'])
@jwt_required()
def get_points_balance():
    """获取金币余额"""
    try:
        identity_str = get_jwt_identity()  # 这是字符串形式的用户ID
        claims = get_jwt()  # 获取claims，包含additional_claims
        
        # 从claims中获取type和id
        user_type = claims.get('type', 'user')
        user_id = claims.get('id') or int(identity_str)
        
        if user_type != 'user':
            return jsonify({
                'success': False,
                'message': '无效的Token',
                'data': None
            }), 401
        
        # 使用session.query()确保获取最新数据
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'data': None
            }), 404
        
        current_points = float(user.points) if user.points is not None else 0.0
        print(f'[DEBUG] get_points_balance - 用户ID: {user_id}, 金币余额: {current_points}')
        
        return jsonify({
            'success': True,
            'data': {
                'points': current_points
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取金币余额失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/orders/statistics', methods=['GET'])
@jwt_required()
def get_order_statistics():
    """获取订单统计信息"""
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
        
        from datetime import timedelta
        
        today = date.today()
        first_day_of_month = date(today.year, today.month, 1)
        
        # 今日报单数（按settlement_date统计）
        today_order_count = Order.query.filter_by(
            user_id=user_id,
            status='approved'
        ).filter(
            Order.settlement_date == today
        ).count()
        
        print(f'[DEBUG] get_order_statistics - 用户ID: {user_id}, 今日日期: {today}, 今日订单数: {today_order_count}')
        
        # 本月报单数
        month_order_count = Order.query.filter_by(
            user_id=user_id,
            status='approved'
        ).filter(
            Order.settlement_date >= first_day_of_month,
            Order.settlement_date <= today
        ).count()
        
        return jsonify({
            'success': True,
            'data': {
                'todayOrderCount': today_order_count,
                'monthOrderCount': month_order_count
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取订单统计失败: {str(e)}',
            'data': None
        }), 500

