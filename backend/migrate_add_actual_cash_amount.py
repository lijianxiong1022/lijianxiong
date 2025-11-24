#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""添加actual_cash_amount字段到transactions表"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import db
from sqlalchemy import inspect, text

def calculate_recharge_price(points_amount, exchange_rate, discount_rules):
    """计算充值所需现金（考虑优惠）"""
    # 找到适用的优惠规则
    applicable_rule = None
    for rule in sorted(discount_rules, key=lambda x: x.get('minAmount', 0), reverse=True):
        if points_amount >= rule.get('minAmount', 0):
            applicable_rule = rule
            break
    
    # 计算基础现金（根据兑换比例）
    base_cash = points_amount * exchange_rate
    
    # 应用优惠折扣
    if applicable_rule:
        discount = applicable_rule.get('discount', 100) / 100.0  # 转换为小数，例如98折=0.98
        actual_cash = base_cash * discount
    else:
        actual_cash = base_cash
    
    return round(actual_cash, 2)

def migrate():
    app = create_app()
    with app.app_context():
        try:
            # 检查字段是否已存在
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('transactions')]
            
            print(f'当前transactions表字段: {columns}')
            
            if 'actual_cash_amount' in columns:
                print('[OK] actual_cash_amount字段已存在，无需添加')
                return
            
            # 添加字段
            print('正在添加actual_cash_amount字段...')
            db.session.execute(text('ALTER TABLE transactions ADD COLUMN actual_cash_amount NUMERIC(10, 2) NULL'))
            db.session.commit()
            print('[OK] actual_cash_amount字段添加成功')
            
            # 为现有的充值记录计算并更新actual_cash_amount
            print('正在更新现有充值记录的actual_cash_amount...')
            from models import Transaction, SystemSetting
            import json
            
            # 获取系统设置
            settings_obj = SystemSetting.query.filter_by(setting_key='system_config').first()
            if settings_obj:
                settings = json.loads(settings_obj.setting_value)
                exchange_rate = float(settings.get('coinExchangeRate', 10.0))
                recharge_discount_rules = settings.get('rechargeDiscountRules', [])
            else:
                exchange_rate = 10.0
                recharge_discount_rules = []
            
            # 更新所有充值记录
            recharge_transactions = Transaction.query.filter_by(transaction_type='recharge').all()
            updated_count = 0
            
            for trans in recharge_transactions:
                if not trans.actual_cash_amount and trans.points_change:
                    points_amount = float(trans.points_change)
                    actual_cash = calculate_recharge_price(points_amount, exchange_rate, recharge_discount_rules)
                    trans.actual_cash_amount = actual_cash
                    updated_count += 1
            
            db.session.commit()
            print(f'[OK] 已更新 {updated_count} 条充值记录的actual_cash_amount')
            
        except Exception as e:
            print(f'[ERROR] 迁移失败: {str(e)}')
            db.session.rollback()
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    migrate()
    print('迁移完成！')
