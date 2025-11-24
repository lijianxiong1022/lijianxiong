#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""添加unit_price字段到transactions表"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import db
from sqlalchemy import inspect, text

def migrate():
    app = create_app()
    with app.app_context():
        try:
            # 检查字段是否已存在
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('transactions')]
            
            print(f'当前transactions表字段: {columns}')
            
            if 'unit_price' in columns:
                print('[OK] unit_price字段已存在，无需添加')
                return
            
            # 添加字段
            print('正在添加unit_price字段...')
            db.session.execute(text('ALTER TABLE transactions ADD COLUMN unit_price NUMERIC(10, 2) NULL'))
            db.session.commit()
            print('[OK] unit_price字段添加成功')
            
        except Exception as e:
            print(f'[ERROR] 迁移失败: {str(e)}')
            db.session.rollback()
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    migrate()

