from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import db, SystemSetting, Admin
from utils import get_system_settings
from api import api_bp
import json

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

@api_bp.route('/admin/settings', methods=['GET'])
@jwt_required()
def get_settings():
    """获取系统配置（管理员）"""
    try:
        admin, error_response, status_code = check_admin_auth()
        if error_response:
            return error_response, status_code
        
        settings = get_system_settings()
        
        return jsonify({
            'success': True,
            'data': settings
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取配置失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/user/settings', methods=['GET'])
@jwt_required()
def get_user_settings():
    """获取系统配置（用户端，只返回公开配置）"""
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
        
        # 获取系统设置
        settings = get_system_settings()
        
        # 只返回用户需要的配置（不包含管理员配置）
        user_settings = {
            'price': settings.get('price', {}),
            'discountRules': settings.get('discountRules', []),
            'rewardRates': settings.get('rewardRates', {}),
            'transferLimits': settings.get('transferLimits', {}),
            'coinExchangeRate': settings.get('coinExchangeRate', 10.0),
            'rechargeDiscountRules': settings.get('rechargeDiscountRules', [])
        }
        
        return jsonify({
            'success': True,
            'data': user_settings
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取配置失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/admin/settings', methods=['PUT'])
@jwt_required()
def update_settings():
    """更新系统配置"""
    try:
        admin, error_response, status_code = check_admin_auth()
        if error_response:
            return error_response, status_code
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空',
                'data': None
            }), 400
        
        # 获取现有配置或使用默认配置
        current_settings = get_system_settings()
        
        # 合并新配置
        if 'contact' in data:
            current_settings['contact'] = data['contact']
        if 'price' in data:
            price_config = data['price']
            if 'basePrice' in price_config:
                price_config['basePrice'] = float(price_config['basePrice'])
            if 'fridayPrice' in price_config:
                price_config['fridayPrice'] = float(price_config['fridayPrice'])
            current_settings['price'] = price_config
        if 'coinExchangeRate' in data:
            current_settings['coinExchangeRate'] = float(data['coinExchangeRate'])
        if 'discountRules' in data:
            current_settings['discountRules'] = data['discountRules']
        if 'rewardRates' in data:
            reward_rates = data['rewardRates']
            # 前端已经将百分比转换为小数（除以100），后端直接使用，不再转换
            if 'direct' in reward_rates:
                reward_rates['direct'] = float(reward_rates['direct'])  # 前端已转换，直接使用
            if 'indirect' in reward_rates:
                reward_rates['indirect'] = float(reward_rates['indirect'])  # 前端已转换，直接使用
            current_settings['rewardRates'] = reward_rates
        if 'transferLimits' in data:
            # 确保数值类型正确
            transfer_limits = data['transferLimits']
            if 'minQuantity' in transfer_limits:
                transfer_limits['minQuantity'] = float(transfer_limits['minQuantity'])
            if 'maxUnitPrice' in transfer_limits:
                transfer_limits['maxUnitPrice'] = float(transfer_limits['maxUnitPrice'])
            current_settings['transferLimits'] = transfer_limits
        if 'rechargeDiscountRules' in data:
            current_settings['rechargeDiscountRules'] = data['rechargeDiscountRules']
        
        # 保存到数据库
        settings_obj = SystemSetting.query.filter_by(setting_key='system_config').first()
        if settings_obj:
            settings_obj.setting_value = json.dumps(current_settings, ensure_ascii=False)
        else:
            settings_obj = SystemSetting(
                setting_key='system_config',
                setting_value=json.dumps(current_settings, ensure_ascii=False)
            )
            db.session.add(settings_obj)
        
        db.session.commit()
        # 提交后清除缓存，确保下次读取时获取最新数据
        db.session.expire_all()
        
        return jsonify({
            'success': True,
            'message': '配置更新成功',
            'data': current_settings
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'更新配置失败: {str(e)}',
            'data': None
        }), 500

