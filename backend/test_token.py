#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试JWT Token生成和验证
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

jwt = JWTManager(app)

@app.route('/test/create-token', methods=['GET'])
def test_create_token():
    """测试创建token"""
    token = create_access_token(identity={'id': 4, 'type': 'user'})
    return {
        'token': token,
        'token_length': len(token),
        'token_preview': token[:50] + '...'
    }

@app.route('/test/verify-token', methods=['GET'])
@jwt_required()
def test_verify_token():
    """测试验证token"""
    identity = get_jwt_identity()
    return {
        'identity': identity,
        'type': identity.get('type') if identity else None,
        'id': identity.get('id') if identity else None
    }

if __name__ == '__main__':
    print('=' * 50)
    print('JWT Token 测试工具')
    print('=' * 50)
    print(f'JWT_SECRET_KEY: {app.config["JWT_SECRET_KEY"][:20]}...')
    print(f'JWT_ACCESS_TOKEN_EXPIRES: {app.config["JWT_ACCESS_TOKEN_EXPIRES"]}')
    print('=' * 50)
    print('\n启动测试服务器...')
    print('访问 http://localhost:5001/test/create-token 创建token')
    print('使用创建的token访问 http://localhost:5001/test/verify-token')
    print('=' * 50)
    app.run(port=5001, debug=True)

