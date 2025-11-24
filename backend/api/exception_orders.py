from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import json
from models import db, User, Order, ExceptionOrder
from api import api_bp

# 允许的图片扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@api_bp.route('/exception-orders', methods=['POST'])
@jwt_required()
def create_exception_order():
    """提交异常订单"""
    try:
        identity_str = get_jwt_identity()
        claims = get_jwt()
        
        user_type = claims.get('type', 'user')
        user_id = claims.get('id') or int(identity_str)
        
        if user_type != 'user':
            return jsonify({
                'success': False,
                'message': '无效的Token',
                'data': None
            }), 401
        
        # 获取表单数据
        order_id = request.form.get('orderId')
        description = request.form.get('description')
        
        if not order_id or not description:
            return jsonify({
                'success': False,
                'message': '订单ID和异常说明为必填项',
                'data': None
            }), 400
        
        # 验证订单是否存在且属于当前用户
        order = Order.query.filter_by(id=order_id, user_id=user_id).first()
        if not order:
            return jsonify({
                'success': False,
                'message': '订单不存在或不属于当前用户',
                'data': None
            }), 404
        
        # 检查是否已经提交过异常订单
        existing_exception = ExceptionOrder.query.filter_by(order_id=order_id).first()
        if existing_exception:
            return jsonify({
                'success': False,
                'message': '该订单已提交过异常报单',
                'data': None
            }), 400
        
        # 处理图片上传
        image_urls = []
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    # 生成安全的文件名
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    unique_filename = f"{timestamp}_{filename}"
                    
                    # 创建上传目录
                    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'exception_orders')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # 保存文件
                    file_path = os.path.join(upload_dir, unique_filename)
                    file.save(file_path)
                    
                    # 生成URL（相对路径）
                    image_url = f"/uploads/exception_orders/{unique_filename}"
                    image_urls.append(image_url)
        
        # 创建异常订单
        exception_order = ExceptionOrder(
            order_id=order_id,
            user_id=user_id,
            description=description,
            image_urls=json.dumps(image_urls) if image_urls else None,
            status='pending'
        )
        
        db.session.add(exception_order)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '异常订单提交成功',
            'data': exception_order.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'提交异常订单失败: {str(e)}',
            'data': None
        }), 500

