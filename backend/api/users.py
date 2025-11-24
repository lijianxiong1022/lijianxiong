from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import db, User, NonMember
from api import api_bp

@api_bp.route('/users/nonmembers', methods=['GET'])
@jwt_required()
def get_nonmembers():
    """获取非会员列表"""
    try:
        identity_str = get_jwt_identity()  # 这是字符串形式的用户ID
        claims = get_jwt()  # 获取claims，包含additional_claims
        print(f'[DEBUG] get_nonmembers - identity: {identity_str}, claims: {claims}')
        
        # 从claims中获取type和id
        user_type = claims.get('type', 'user')
        user_id = claims.get('id') or int(identity_str)
        
        if user_type != 'user':
            print(f'[DEBUG] get_nonmembers - 无效的Token类型: {user_type}')
            return jsonify({
                'success': False,
                'message': '无效的Token',
                'data': None
            }), 401
        non_members = NonMember.query.filter_by(owner_id=user_id).order_by(NonMember.created_at.desc()).all()
        
        print(f'[DEBUG] get_nonmembers - 成功获取非会员列表，用户ID: {user_id}, 数量: {len(non_members)}')
        return jsonify({
            'success': True,
            'data': {
                'list': [nm.to_dict() for nm in non_members]
            }
        })
        
    except Exception as e:
        print(f'[DEBUG] get_nonmembers - 异常: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取非会员列表失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/users/nonmembers', methods=['POST'])
@jwt_required()
def add_nonmember():
    """添加非会员"""
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
        data = request.get_json()
        
        name = data.get('name', '').strip()
        link = data.get('link', '').strip()
        
        if not name:
            return jsonify({
                'success': False,
                'message': '姓名不能为空',
                'data': None
            }), 400
        
        # 检查同一用户下是否有重复的名称
        existing_by_name = NonMember.query.filter_by(owner_id=user_id, name=name).first()
        if existing_by_name:
            return jsonify({
                'success': False,
                'message': '该名称已存在，请使用其他名称',
                'data': None
            }), 400
        
        # 检查同一用户下是否有重复的链接（如果链接不为空）
        if link:
            existing_by_link = NonMember.query.filter_by(owner_id=user_id, link=link).first()
            if existing_by_link:
                return jsonify({
                    'success': False,
                    'message': '该链接已存在，请使用其他链接',
                    'data': None
                }), 400
        
        # 创建非会员
        non_member = NonMember(
            name=name,
            link=link,
            owner_id=user_id
        )
        
        db.session.add(non_member)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '添加成功',
            'data': non_member.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'添加失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/users/nonmembers/<int:nonmember_id>', methods=['DELETE'])
@jwt_required()
def delete_nonmember(nonmember_id):
    """删除非会员"""
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
        non_member = NonMember.query.filter_by(id=nonmember_id, owner_id=user_id).first()
        
        if not non_member:
            return jsonify({
                'success': False,
                'message': '非会员不存在或无权删除',
                'data': None
            }), 404
        
        db.session.delete(non_member)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '删除成功',
            'data': None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/users/subordinates', methods=['GET'])
@jwt_required()
def get_subordinates():
    """获取用户的下级（普通会员和代理会员）"""
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
        
        # 获取当前用户
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'data': None
            }), 404
        
        # 普通会员（下级）
        ordinary_members = User.query.filter(
            User.parent_id == user_id,
            User.user_type == 'ordinary'
        ).order_by(User.register_date.desc()).all()
        
        ordinary_list = []
        for member in ordinary_members:
            # 获取非会员数量
            nonmember_count = NonMember.query.filter_by(owner_id=member.id).count()
            ordinary_list.append({
                'id': member.promo_code,
                'name': member.name,
                'phone': member.phone,  # 返回完整手机号，用于转账
                'phoneDisplay': member.phone[:3] + '****' + member.phone[-4:],  # 显示时隐藏部分手机号
                'registerDate': member.register_date.strftime('%Y-%m-%d') if member.register_date else None,
                'points': float(member.points) if member.points else 0.0,
                'nonmemberCount': nonmember_count
            })
        
        # 代理会员（下级）
        agent_members = []
        if user.user_type == 'agent':
            # 只有代理用户才能看到下级代理
            agent_members_query = User.query.filter(
                User.parent_id == user_id,
                User.user_type == 'agent'
            ).order_by(User.register_date.desc()).all()
            
            for agent in agent_members_query:
                # 获取非会员数量
                nonmember_count = NonMember.query.filter_by(owner_id=agent.id).count()
                agent_members.append({
                    'id': agent.promo_code,
                    'name': agent.name,
                    'phone': agent.phone,  # 返回完整手机号，用于转账
                    'phoneDisplay': agent.phone[:3] + '****' + agent.phone[-4:],  # 显示时隐藏部分手机号
                    'registerDate': agent.register_date.strftime('%Y-%m-%d') if agent.register_date else None,
                    'points': float(agent.points) if agent.points else 0.0,
                    'nonmemberCount': nonmember_count
                })
        
        return jsonify({
            'success': True,
            'data': {
                'ordinaryMembers': ordinary_list,
                'agentMembers': agent_members
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取下级用户失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/users/upgrade-to-agent', methods=['POST'])
@jwt_required()
def upgrade_to_agent():
    """用户升级为代理"""
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
        
        # 获取当前用户
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'data': None
            }), 404
        
        # 检查是否已经是代理
        if user.user_type == 'agent':
            return jsonify({
                'success': False,
                'message': '您已经是代理用户',
                'data': None
            }), 400
        
        # 升级为代理
        user.user_type = 'agent'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '升级为代理成功',
            'data': {
                'userType': 'agent'
            }
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'升级失败: {str(e)}',
            'data': None
        }), 500

