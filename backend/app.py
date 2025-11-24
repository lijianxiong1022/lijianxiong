from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_jwt_extended.exceptions import JWTDecodeError, NoAuthorizationError, InvalidHeaderError
from config import Config
from models import db
from api import api_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化扩展
    db.init_app(app)
    jwt = JWTManager(app)
    CORS(app)  # 允许跨域请求
    
    # 添加请求日志中间件（仅用于调试）
    @app.before_request
    def log_request_info():
        if app.config.get('DEBUG'):
            from flask import request
            auth_header = request.headers.get('Authorization', 'None')
            print(f'[DEBUG] 请求: {request.method} {request.path}')
            print(f'[DEBUG] Authorization头: {auth_header[:50] if auth_header != "None" else "None"}...')
    
    # JWT错误处理器
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'message': 'Token已过期，请重新登录',
            'data': None
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        print(f'[DEBUG] JWT invalid_token_loader - error: {error}')
        return jsonify({
            'success': False,
            'message': f'无效的Token，请重新登录: {str(error)}',
            'data': None
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        print(f'[DEBUG] JWT unauthorized_loader - error: {error}')
        return jsonify({
            'success': False,
            'message': '缺少Token，请先登录',
            'data': None
        }), 401
    
    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'message': 'Token需要刷新',
            'data': None
        }), 401
    
    # 注册蓝图
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    # 配置静态文件服务（用于上传的图片）
    from flask import send_from_directory
    import os
    
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
        return send_from_directory(uploads_dir, filename)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )

