from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, date, timedelta
from models import db, User, Admin, Order, Transaction, NonMember, ExceptionOrder
from utils import hash_password, hash_pay_password, verify_password
from api import api_bp
from sqlalchemy import func, and_, or_

def check_admin_auth():
    """检查管理员权限"""
    identity_str = get_jwt_identity()
    claims = get_jwt()
    admin_type = claims.get('type', '')
    admin_id = claims.get('id') or (int(identity_str) if identity_str.isdigit() else None)
    
    if admin_type != 'admin':
        return None, jsonify({
            'success': False,
            'message': '需要管理员权限',
            'data': None
        }), 403
    
    admin = Admin.query.get(admin_id)
    if not admin:
        return None, jsonify({
            'success': False,
            'message': '管理员不存在',
            'data': None
        }), 404
    
    return admin, None, None

@api_bp.route('/admin/agents', methods=['POST'])
@jwt_required()
def create_agent():
    """管理员创建代理"""
    try:
        admin, error_response, status_code = check_admin_auth()
        if error_response:
            return error_response, status_code
        
        data = request.get_json()
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        
        # 验证必填字段
        if not name:
            return jsonify({
                'success': False,
                'message': '代理姓名不能为空',
                'data': None
            }), 400
        
        if not phone or not phone.isdigit() or len(phone) != 11 or not phone.startswith('1'):
            return jsonify({
                'success': False,
                'message': '手机号格式不正确',
                'data': None
            }), 400
        
        # 检查手机号是否已注册
        if User.query.filter_by(phone=phone).first():
            return jsonify({
                'success': False,
                'message': '该手机号已被注册',
                'data': None
            }), 400
        
        # 查找平台用户（推广码888888）
        platform_user = User.query.filter_by(promo_code='888888').first()
        if not platform_user:
            return jsonify({
                'success': False,
                'message': '平台用户不存在，请先初始化数据库',
                'data': None
            }), 500
        
        # 生成用户推广码
        user_promo_code = User.generate_promo_code()
        
        # 创建代理用户（默认密码为手机号后6位）
        default_password = phone[-6:]
        default_pay_password = '123456'  # 默认支付密码
        
        user = User(
            promo_code=user_promo_code,
            name=name,
            phone=phone,
            password=hash_password(default_password),
            pay_password=hash_pay_password(default_pay_password),
            parent_id=platform_user.id,  # 上级为平台
            user_type='agent',  # 代理类型
            points=0
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '代理创建成功',
            'data': {
                'id': user.id,
                'promoCode': user.promo_code,
                'name': user.name,
                'phone': user.phone,
                'defaultPassword': default_password,
                'defaultPayPassword': default_pay_password
            }
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'创建代理失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/admin/members', methods=['GET'])
@jwt_required()
def get_members():
    """获取会员列表（管理员）"""
    try:
        admin, error_response, status_code = check_admin_auth()
        if error_response:
            return error_response, status_code
        
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 20))
        promo_code = request.args.get('id', '').strip()
        phone = request.args.get('phone', '').strip()
        register_date = request.args.get('date', '').strip()
        
        # 构建查询
        query = User.query.filter_by(user_type='ordinary')
        
        if promo_code:
            query = query.filter(User.promo_code.like(f'%{promo_code}%'))
        if phone:
            query = query.filter(User.phone.like(f'%{phone}%'))
        if register_date:
            try:
                date_obj = datetime.strptime(register_date, '%Y-%m-%d').date()
                query = query.filter(func.date(User.register_date) == date_obj)
            except:
                pass
        
        # 总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        users = query.order_by(User.register_date.desc()).offset(offset).limit(page_size).all()
        
        # 计算统计数据
        result_list = []
        for user in users:
            # 今日报单数
            today = date.today()
            today_orders = Order.query.filter(
                and_(
                    Order.user_id == user.id,
                    func.date(Order.settlement_date) == today
                )
            ).count()
            
            # 本月报单数
            month_start = date(today.year, today.month, 1)
            month_orders = Order.query.filter(
                and_(
                    Order.user_id == user.id,
                    func.date(Order.settlement_date) >= month_start
                )
            ).count()
            
            # 非会员数
            nonmember_count = NonMember.query.filter_by(owner_id=user.id).count()
            
            result_list.append({
                'id': user.promo_code,
                'name': user.name,
                'phone': user.phone,  # 管理员可以看到完整手机号
                'type': '普通会员',
                'parentId': user.parent.promo_code if user.parent else None,
                'points': float(user.points),
                'registerDate': user.register_date.strftime('%Y-%m-%d') if user.register_date else None,
                'todayOrders': today_orders,
                'monthOrders': month_orders,
                'nonmemberCount': nonmember_count
            })
        
        return jsonify({
            'success': True,
            'data': {
                'list': result_list,
                'total': total,
                'page': page,
                'pageSize': page_size
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取会员列表失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/admin/agents', methods=['GET'])
@jwt_required()
def get_agents():
    """获取代理列表（管理员）"""
    try:
        admin, error_response, status_code = check_admin_auth()
        if error_response:
            return error_response, status_code
        
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 20))
        promo_code = request.args.get('id', '').strip()
        phone = request.args.get('phone', '').strip()
        register_date = request.args.get('date', '').strip()
        
        # 构建查询
        query = User.query.filter_by(user_type='agent')
        
        # 排除平台用户（推广码888888）
        query = query.filter(User.promo_code != '888888')
        
        if promo_code:
            query = query.filter(User.promo_code.like(f'%{promo_code}%'))
        if phone:
            query = query.filter(User.phone.like(f'%{phone}%'))
        if register_date:
            try:
                date_obj = datetime.strptime(register_date, '%Y-%m-%d').date()
                query = query.filter(func.date(User.register_date) == date_obj)
            except:
                pass
        
        # 总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        users = query.order_by(User.register_date.desc()).offset(offset).limit(page_size).all()
        
        # 计算统计数据
        result_list = []
        today = date.today()
        month_start = date(today.year, today.month, 1)
        
        for user in users:
            # 下级代理数
            sub_agents = User.query.filter(
                and_(
                    User.parent_id == user.id,
                    User.user_type == 'agent'
                )
            ).count()
            
            # 下级会员数
            sub_members = User.query.filter(
                and_(
                    User.parent_id == user.id,
                    User.user_type == 'ordinary'
                )
            ).count()
            
            # 非会员数
            nonmember_count = NonMember.query.filter_by(owner_id=user.id).count()
            
            # 今日报单数
            today_orders = Order.query.filter(
                and_(
                    Order.user_id == user.id,
                    func.date(Order.settlement_date) == today
                )
            ).count()
            
            # 本月报单数
            month_orders = Order.query.filter(
                and_(
                    Order.user_id == user.id,
                    func.date(Order.settlement_date) >= month_start
                )
            ).count()
            
            result_list.append({
                'id': user.promo_code,
                'name': user.name,
                'phone': user.phone,  # 管理员可以看到完整手机号
                'type': '代理',
                'parentId': user.parent.promo_code if user.parent else None,
                'points': float(user.points),
                'registerDate': user.register_date.strftime('%Y-%m-%d') if user.register_date else None,
                'subAgents': sub_agents,
                'subMembers': sub_members,
                'nonmemberCount': nonmember_count,
                'todayOrders': today_orders,
                'monthOrders': month_orders
            })
        
        return jsonify({
            'success': True,
            'data': {
                'list': result_list,
                'total': total,
                'page': page,
                'pageSize': page_size
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取代理列表失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/admin/orders', methods=['GET'])
@jwt_required()
def get_admin_orders():
    """获取订单列表（管理员）"""
    try:
        admin, error_response, status_code = check_admin_auth()
        if error_response:
            return error_response, status_code
        
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 20))
        settlement_date_str = request.args.get('settlementDate', '').strip()
        promo_code = request.args.get('id', '').strip()
        phone = request.args.get('phone', '').strip()
        exported = request.args.get('exported', '').strip()
        
        # 构建查询
        query = Order.query.join(User, Order.user_id == User.id)
        
        # 报单日期筛选
        if settlement_date_str:
            try:
                settlement_date = datetime.strptime(settlement_date_str, '%Y-%m-%d').date()
                query = query.filter(Order.settlement_date == settlement_date)
            except ValueError:
                pass  # 日期格式错误，忽略该筛选条件
        
        if promo_code:
            query = query.filter(User.promo_code.like(f'%{promo_code}%'))
        if phone:
            query = query.filter(User.phone.like(f'%{phone}%'))
        if exported == 'true':
            query = query.filter(Order.exported == True)
        elif exported == 'false':
            query = query.filter(Order.exported == False)
        
        # 总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        orders = query.order_by(Order.created_at.desc()).offset(offset).limit(page_size).all()
        
        result_list = []
        for order in orders:
            user = order.user
            nonmember = NonMember.query.get(order.non_member_id) if order.non_member_id else None
            
            result_list.append({
                'id': order.id,
                'promoCode': user.promo_code,
                'name': user.name,
                'phone': user.phone,  # 管理员可以看到完整手机号
                'settlementDate': order.settlement_date.strftime('%Y-%m-%d') if order.settlement_date else None,
                'nonMemberName': nonmember.name if nonmember else '-',
                'nonMemberLink': nonmember.link if nonmember else '-',
                'points': float(order.total_points),
                'createdAt': order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else None,
                'exported': order.exported
            })
        
        return jsonify({
            'success': True,
            'data': {
                'list': result_list,
                'total': total,
                'page': page,
                'pageSize': page_size
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

@api_bp.route('/admin/orders/export', methods=['POST'])
@jwt_required()
def export_orders():
    """导出订单（标记为已导出）"""
    try:
        admin, error_response, status_code = check_admin_auth()
        if error_response:
            return error_response, status_code
        
        data = request.get_json()
        order_ids = data.get('orderIds', [])
        
        if not order_ids:
            return jsonify({
                'success': False,
                'message': '请选择要导出的订单',
                'data': None
            }), 400
        
        # 标记为已导出，并将状态改为approved（已通过）
        Order.query.filter(Order.id.in_(order_ids)).update(
            {Order.exported: True, Order.status: 'approved'},
            synchronize_session=False
        )
        # 如果有异常订单，也将异常订单状态改为exported
        ExceptionOrder.query.filter(ExceptionOrder.order_id.in_(order_ids)).update(
            {ExceptionOrder.status: 'exported'},
            synchronize_session=False
        )
        db.session.commit()
        
        # 获取导出的订单数据
        orders = Order.query.filter(Order.id.in_(order_ids)).all()
        
        # 生成CSV格式数据
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头（使用UTF-8 BOM以支持中文）
        output.write('\ufeff')  # UTF-8 BOM
        writer.writerow(['推广码', '姓名', '手机号', '直推用户姓名', '直推用户链接', '消耗金币', '提交时间'])
        
        # 写入数据
        for order in orders:
            user = order.user
            nonmember = NonMember.query.get(order.non_member_id) if order.non_member_id else None
            writer.writerow([
                user.promo_code,
                user.name,
                user.phone,
                nonmember.name if nonmember else '-',
                nonmember.link if nonmember else '-',
                float(order.total_points),
                order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else '-'
            ])
        
        csv_data = output.getvalue()
        output.close()
        
        return jsonify({
            'success': True,
            'message': '导出成功',
            'data': {
                'csv': csv_data,
                'count': len(orders)
            }
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'导出失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/admin/transactions', methods=['GET'])
@jwt_required()
def get_admin_transactions():
    """获取交易记录列表（管理员）"""
    try:
        admin, error_response, status_code = check_admin_auth()
        if error_response:
            return error_response, status_code
        
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 20))
        promo_code = request.args.get('id', '').strip()
        phone = request.args.get('phone', '').strip()
        transaction_type = request.args.get('type', '').strip()
        
        # 构建查询（排除平台用户888888的奖励记录）
        query = Transaction.query.join(User, Transaction.user_id == User.id)
        
        # 排除平台用户（推广码888888）的奖励记录
        query = query.filter(
            ~((Transaction.transaction_type == 'reward') & (User.promo_code == '888888'))
        )
        
        if promo_code:
            query = query.filter(User.promo_code.like(f'%{promo_code}%'))
        if phone:
            query = query.filter(User.phone.like(f'%{phone}%'))
        if transaction_type:
            query = query.filter(Transaction.transaction_type == transaction_type)
        
        # 总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        transactions = query.order_by(Transaction.created_at.desc()).offset(offset).limit(page_size).all()
        
        result_list = []
        for trans in transactions:
            user = trans.user
            result_list.append({
                'promoCode': user.promo_code,
                'name': user.name,
                'phone': user.phone,  # 管理员可以看到完整手机号
                'transactionType': trans.transaction_type,
                'pointsChange': float(trans.points_change),
                'balance': float(trans.balance),
                'description': trans.description,
                'createdAt': trans.created_at.strftime('%Y-%m-%d %H:%M:%S') if trans.created_at else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'list': result_list,
                'total': total,
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

@api_bp.route('/admin/agents/<promo_code>/subordinates', methods=['GET'])
@jwt_required()
def get_agent_subordinates(promo_code):
    """获取代理的下级（非会员、普通会员、代理会员）"""
    try:
        admin, error_response, status_code = check_admin_auth()
        if error_response:
            return error_response, status_code
        
        # 通过推广码查找用户
        user = User.query.filter_by(promo_code=promo_code).first()
        if not user or user.user_type != 'agent':
            return jsonify({
                'success': False,
                'message': '代理不存在',
                'data': None
            }), 404
        
        user_id = user.id
        
        # 非会员
        nonmembers = NonMember.query.filter_by(owner_id=user_id).all()
        nonmember_list = [{
            'id': nm.id,
            'name': nm.name,
            'link': nm.link or '-',
            'createdAt': nm.created_at.strftime('%Y-%m-%d') if nm.created_at else None
        } for nm in nonmembers]
        
        # 普通会员
        ordinary_members = User.query.filter(
            and_(
                User.parent_id == user_id,
                User.user_type == 'ordinary'
            )
        ).all()
        ordinary_list = []
        for member in ordinary_members:
            nonmember_count = NonMember.query.filter_by(owner_id=member.id).count()
            ordinary_list.append({
                'id': member.promo_code,
                'name': member.name,
                'phone': member.phone,  # 管理员可以看到完整手机号
                'registerDate': member.register_date.strftime('%Y-%m-%d') if member.register_date else None,
                'nonmemberCount': nonmember_count
            })
        
        # 代理会员
        agent_members = User.query.filter(
            and_(
                User.parent_id == user_id,
                User.user_type == 'agent'
            )
        ).all()
        agent_list = []
        for agent in agent_members:
            nonmember_count = NonMember.query.filter_by(owner_id=agent.id).count()
            agent_list.append({
                'id': agent.promo_code,
                'name': agent.name,
                'phone': agent.phone,  # 管理员可以看到完整手机号
                'registerDate': agent.register_date.strftime('%Y-%m-%d') if agent.register_date else None,
                'nonmemberCount': nonmember_count
            })
        
        return jsonify({
            'success': True,
            'data': {
                'nonmembers': nonmember_list,
                'ordinaryMembers': ordinary_list,
                'agentMembers': agent_list
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取下级信息失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/admin/members/<promo_code>', methods=['DELETE'])
@jwt_required()
def delete_member(promo_code):
    """删除会员"""
    try:
        admin, error_response, status_code = check_admin_auth()
        if error_response:
            return error_response, status_code
        
        # 通过推广码查找用户
        user = User.query.filter_by(promo_code=promo_code, user_type='ordinary').first()
        if not user:
            return jsonify({
                'success': False,
                'message': '会员不存在',
                'data': None
            }), 404
        
        # 删除用户
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '删除成功',
            'data': None
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/admin/agents/<promo_code>', methods=['DELETE'])
@jwt_required()
def delete_agent(promo_code):
    """删除代理"""
    try:
        admin, error_response, status_code = check_admin_auth()
        if error_response:
            return error_response, status_code
        
        # 通过推广码查找用户（排除平台用户）
        user = User.query.filter(
            and_(
                User.promo_code == promo_code,
                User.user_type == 'agent',
                User.promo_code != '888888'
            )
        ).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '代理不存在',
                'data': None
            }), 404
        
        # 删除用户
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '删除成功',
            'data': None
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/admin/users/<promo_code>/change-parent', methods=['PUT'])
@jwt_required()
def change_parent(promo_code):
    """更换上级"""
    try:
        admin, error_response, status_code = check_admin_auth()
        if error_response:
            return error_response, status_code
        
        data = request.get_json()
        new_parent_promo_code = data.get('parentPromoCode', '').strip()
        
        if not new_parent_promo_code:
            return jsonify({
                'success': False,
                'message': '请输入新的上级推广码',
                'data': None
            }), 400
        
        # 查找当前用户
        user = User.query.filter_by(promo_code=promo_code).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'data': None
            }), 404
        
        # 查找新上级
        new_parent = User.query.filter_by(promo_code=new_parent_promo_code).first()
        if not new_parent:
            return jsonify({
                'success': False,
                'message': '新上级不存在',
                'data': None
            }), 404
        
        # 验证上级身份
        if user.user_type == 'ordinary':
            # 普通会员更换上级：必须是代理或平台（888888）
            if new_parent.user_type != 'agent' and new_parent.promo_code != '888888':
                return jsonify({
                    'success': False,
                    'message': '普通会员的上级必须是代理或平台',
                    'data': None
                }), 400
            
            # 如果新上级是平台（888888），直接升级为代理
            if new_parent.promo_code == '888888':
                user.user_type = 'agent'
        else:
            # 代理更换上级：必须是代理或平台（888888）
            if new_parent.user_type != 'agent' and new_parent.promo_code != '888888':
                return jsonify({
                    'success': False,
                    'message': '代理的上级必须是代理或平台',
                    'data': None
                }), 400
        
        # 检查是否需要升级
        was_ordinary = user.user_type == 'ordinary'
        upgrade_message = ''
        
        # 更新上级
        user.parent_id = new_parent.id
        
        # 如果普通会员更换上级为平台（888888），直接升级为代理
        if was_ordinary and new_parent.promo_code == '888888':
            user.user_type = 'agent'
            upgrade_message = '，并已升级为代理'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'更换上级成功{upgrade_message}',
            'data': {
                'userType': user.user_type
            }
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'更换上级失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/admin/users/<promo_code>/orders', methods=['GET'])
@jwt_required()
def get_user_orders(promo_code):
    """获取用户的订单历史记录"""
    try:
        admin, error_response, status_code = check_admin_auth()
        if error_response:
            return error_response, status_code
        
        # 通过推广码查找用户
        user = User.query.filter_by(promo_code=promo_code).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'data': None
            }), 404
        
        start_date = request.args.get('startDate', '').strip()
        end_date = request.args.get('endDate', '').strip()
        status = request.args.get('status', '').strip()
        
        # 构建查询
        query = Order.query.filter_by(user_id=user.id)
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(Order.settlement_date >= start_date_obj)
            except:
                pass
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(Order.settlement_date <= end_date_obj)
            except:
                pass
        
        if status:
            query = query.filter(Order.status == status)
        
        orders = query.order_by(Order.settlement_date.desc(), Order.created_at.desc()).all()
        
        result_list = []
        for order in orders:
            nonmember = NonMember.query.get(order.non_member_id) if order.non_member_id else None
            status_map = {
                'pending': '待审核',
                'approved': '已通过',
                'rejected': '已拒绝'
            }
            result_list.append({
                'settlementDate': order.settlement_date.strftime('%Y-%m-%d') if order.settlement_date else None,
                'nonMemberName': nonmember.name if nonmember else '-',
                'points': float(order.total_points),
                'status': status_map.get(order.status, order.status)
            })
        
        return jsonify({
            'success': True,
            'data': {
                'list': result_list
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取用户订单记录失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/admin/statistics/orders', methods=['GET'])
@jwt_required()
def get_admin_order_statistics():
    """获取订单统计信息（管理员）"""
    try:
        admin, error_response, status_code = check_admin_auth()
        if error_response:
            return error_response, status_code
        
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # 今日报单总量
        today_total = Order.query.filter(
            Order.created_at >= today_start,
            Order.created_at <= today_end
        ).count()
        
        # 今日报单总人数（去重）
        today_users = db.session.query(func.count(func.distinct(Order.user_id))).filter(
            Order.created_at >= today_start,
            Order.created_at <= today_end
        ).scalar() or 0
        
        # 今日消耗总金币
        today_points = db.session.query(func.sum(Order.total_points)).filter(
            Order.created_at >= today_start,
            Order.created_at <= today_end
        ).scalar() or 0
        
        return jsonify({
            'success': True,
            'data': {
                'todayTotal': today_total,
                'todayUsers': today_users,
                'todayPoints': float(today_points) if today_points else 0
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

@api_bp.route('/admin/statistics/transactions', methods=['GET'])
@jwt_required()
def get_admin_transaction_statistics():
    """获取交易统计信息（管理员）"""
    try:
        admin, error_response, status_code = check_admin_auth()
        if error_response:
            return error_response, status_code
        
        today = date.today()
        first_day_of_month = date(today.year, today.month, 1)
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        month_start = datetime.combine(first_day_of_month, datetime.min.time())
        month_end = datetime.combine(today, datetime.max.time())
        
        # 今日充值金币
        today_recharge = db.session.query(func.sum(Transaction.points_change)).filter(
            Transaction.transaction_type == 'recharge',
            Transaction.created_at >= today_start,
            Transaction.created_at <= today_end
        ).scalar() or 0
        
        # 今日收益（人民币收益，这里需要根据实际业务逻辑计算）
        # 假设收益 = 充值金额 - 消耗金额（简化处理）
        today_deduction = db.session.query(func.sum(func.abs(Transaction.points_change))).filter(
            Transaction.transaction_type == 'order_deduction',
            Transaction.created_at >= today_start,
            Transaction.created_at <= today_end
        ).scalar() or 0
        today_revenue = float(today_recharge) - float(today_deduction)  # 简化计算
        
        # 今日消耗总金币
        today_consumption = today_deduction
        
        # 本月充值金币
        month_recharge = db.session.query(func.sum(Transaction.points_change)).filter(
            Transaction.transaction_type == 'recharge',
            Transaction.created_at >= month_start,
            Transaction.created_at <= month_end
        ).scalar() or 0
        
        # 本月收益
        month_deduction = db.session.query(func.sum(func.abs(Transaction.points_change))).filter(
            Transaction.transaction_type == 'order_deduction',
            Transaction.created_at >= month_start,
            Transaction.created_at <= month_end
        ).scalar() or 0
        month_revenue = float(month_recharge) - float(month_deduction)  # 简化计算
        
        # 本月消耗总金币
        month_consumption = month_deduction
        
        return jsonify({
            'success': True,
            'data': {
                'today': {
                    'recharge': float(today_recharge),
                    'revenue': today_revenue,
                    'deduction': float(today_consumption)
                },
                'month': {
                    'recharge': float(month_recharge),
                    'revenue': month_revenue,
                    'deduction': float(month_consumption)
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

@api_bp.route('/admin/statistics/exceptions', methods=['GET'])
@jwt_required()
def get_admin_exception_statistics():
    """获取异常订单统计信息（管理员）"""
    try:
        admin, error_response, status_code = check_admin_auth()
        if error_response:
            return error_response, status_code
        
        today = date.today()
        start_datetime = datetime.combine(today, datetime.min.time())
        end_datetime = datetime.combine(today, datetime.max.time())
        
        # 今日异常订单总数
        today_exceptions = ExceptionOrder.query.filter(
            ExceptionOrder.created_at >= start_datetime,
            ExceptionOrder.created_at <= end_datetime
        ).count()
        
        # 今日待处理
        today_pending = ExceptionOrder.query.filter(
            ExceptionOrder.created_at >= start_datetime,
            ExceptionOrder.created_at <= end_datetime,
            ExceptionOrder.status == 'pending'
        ).count()
        
        # 今日已处理
        today_processed = ExceptionOrder.query.filter(
            ExceptionOrder.created_at >= start_datetime,
            ExceptionOrder.created_at <= end_datetime,
            ExceptionOrder.status == 'exported'
        ).count()
        
        return jsonify({
            'success': True,
            'data': {
                'todayExceptions': today_exceptions,
                'todayPending': today_pending,
                'todayProcessed': today_processed
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取异常订单统计失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/admin/exceptions', methods=['GET'])
@jwt_required()
def get_exceptions():
    """获取异常订单列表（管理员）"""
    try:
        admin, error_response, status_code = check_admin_auth()
        if error_response:
            return error_response, status_code
        
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 20))
        search_date = request.args.get('date', '').strip()
        status_filter = request.args.get('status', '').strip()
        
        # 构建查询
        query = ExceptionOrder.query.join(Order).join(User)
        
        # 日期筛选
        if search_date:
            try:
                date_obj = datetime.strptime(search_date, '%Y-%m-%d').date()
                start_datetime = datetime.combine(date_obj, datetime.min.time())
                end_datetime = datetime.combine(date_obj, datetime.max.time())
                query = query.filter(
                    ExceptionOrder.created_at >= start_datetime,
                    ExceptionOrder.created_at <= end_datetime
                )
            except ValueError:
                pass
        
        # 状态筛选
        if status_filter:
            if status_filter == 'pending':
                query = query.filter(ExceptionOrder.status == 'pending')
            elif status_filter == 'exported' or status_filter == 'processed':
                query = query.filter(ExceptionOrder.status == 'exported')
        
        # 总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        exception_orders = query.order_by(ExceptionOrder.created_at.desc()).offset(offset).limit(page_size).all()
        
        result_list = []
        for ex_order in exception_orders:
            order = ex_order.order
            user = order.user
            nonmember = NonMember.query.get(order.non_member_id) if order.non_member_id else None
            
            import json
            image_urls = []
            if ex_order.image_urls:
                try:
                    image_urls = json.loads(ex_order.image_urls)
                except:
                    image_urls = []
            
            result_list.append({
                'id': ex_order.id,
                'orderId': ex_order.order_id,
                'promoCode': user.promo_code,
                'name': user.name,
                'phone': user.phone,
                'nonMemberName': nonmember.name if nonmember else '-',
                'nonMemberLink': nonmember.link if nonmember else '-',
                'description': ex_order.description,
                'imageUrls': image_urls,
                'status': ex_order.status,
                'statusText': '待处理' if ex_order.status == 'pending' else '已受理',
                'createdAt': ex_order.created_at.strftime('%Y-%m-%d %H:%M:%S') if ex_order.created_at else None,
                'orderSettlementDate': order.settlement_date.strftime('%Y-%m-%d') if order.settlement_date else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'list': result_list,
                'total': total,
                'page': page,
                'pageSize': page_size
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取异常订单失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/admin/users/<promo_code>/reset-password', methods=['PUT'])
@jwt_required()
def reset_user_password(promo_code):
    """重置用户登录密码"""
    try:
        admin, error_response, status_code = check_admin_auth()
        if error_response:
            return error_response, status_code
        
        # 通过推广码查找用户
        user = User.query.filter_by(promo_code=promo_code).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'data': None
            }), 404
        
        # 重置密码为123456
        user.password = hash_password('123456')
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '重置登录密码成功，新密码为：123456',
            'data': None
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'重置密码失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/admin/users/<promo_code>/reset-pay-password', methods=['PUT'])
@jwt_required()
def reset_user_pay_password(promo_code):
    """重置用户支付密码"""
    try:
        admin, error_response, status_code = check_admin_auth()
        if error_response:
            return error_response, status_code
        
        # 通过推广码查找用户
        user = User.query.filter_by(promo_code=promo_code).first()
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'data': None
            }), 404
        
        # 重置支付密码为123456
        user.pay_password = hash_pay_password('123456')
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '重置支付密码成功，新密码为：123456',
            'data': None
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'重置支付密码失败: {str(e)}',
            'data': None
        }), 500

