#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试settings路由是否正确注册"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

app = create_app()

print("检查settings路由:")
with app.app_context():
    from flask import url_for
    routes = []
    for rule in app.url_map.iter_rules():
        if 'settings' in rule.rule:
            routes.append(f"{rule.rule} - {list(rule.methods)}")
    
    if routes:
        print("[OK] 找到settings路由:")
        for route in routes:
            print(f"  - {route}")
    else:
        print("[ERROR] 未找到settings路由!")
        print("\n所有API路由:")
        for rule in app.url_map.iter_rules():
            if '/api/v1' in rule.rule:
                print(f"  - {rule.rule} - {list(rule.methods)}")

