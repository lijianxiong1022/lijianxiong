from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime
from models import db, ExceptionOrder, Order, User, NonMember
from api import api_bp

@api_bp.route('/admin/exceptions/export', methods=['POST'])
@jwt_required()
def export_exceptions():
    """导出异常订单（标记为已导出）"""
    try:
        from api.admin_management import check_admin_auth
        admin, error_response, status_code = check_admin_auth()
        if error_response:
            return error_response, status_code
        
        data = request.get_json()
        exception_ids = data.get('exceptionIds', [])
        
        if not exception_ids:
            return jsonify({
                'success': False,
                'message': '请选择要导出的异常订单',
                'data': None
            }), 400
        
        # 标记为已导出
        ExceptionOrder.query.filter(ExceptionOrder.id.in_(exception_ids)).update(
            {ExceptionOrder.status: 'exported'},
            synchronize_session=False
        )
        db.session.commit()
        
        # 获取导出的异常订单数据
        exception_orders = ExceptionOrder.query.filter(ExceptionOrder.id.in_(exception_ids)).all()
        
        # 生成CSV格式数据
        import csv
        import io
        import json as json_lib
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头（使用UTF-8 BOM以支持中文）
        output.write('\ufeff')  # UTF-8 BOM
        writer.writerow(['推广码', '姓名', '手机号', '直推用户姓名', '直推用户链接', '报单日期', '提交时间', '异常说明', '图片', '处理状态'])
        
        # 写入数据
        for ex_order in exception_orders:
            order = ex_order.order
            user = order.user
            nonmember = NonMember.query.get(order.non_member_id) if order.non_member_id else None
            
            # 处理图片URL
            image_urls = []
            if ex_order.image_urls:
                try:
                    image_urls = json_lib.loads(ex_order.image_urls)
                except:
                    image_urls = []
            image_str = '; '.join(image_urls) if image_urls else '-'
            
            writer.writerow([
                user.promo_code,
                user.name,
                user.phone,
                nonmember.name if nonmember else '-',
                nonmember.link if nonmember else '-',
                order.settlement_date.strftime('%Y-%m-%d') if order.settlement_date else '-',
                ex_order.created_at.strftime('%Y-%m-%d %H:%M:%S') if ex_order.created_at else '-',
                ex_order.description,
                image_str,
                '已导出'
            ])
        
        csv_data = output.getvalue()
        output.close()
        
        return jsonify({
            'success': True,
            'message': '导出成功',
            'data': {
                'csv': csv_data,
                'count': len(exception_orders)
            }
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'导出异常订单失败: {str(e)}',
            'data': None
        }), 500

