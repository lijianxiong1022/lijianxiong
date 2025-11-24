#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修复充值记录的actual_cash_amount"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import create_app
from models import db, Transaction, SystemSetting
from utils import get_system_settings, calculate_recharge_price
import json

app = create_app()
with app.app_context():
    try:
        # 获取系统配置
        settings = get_system_settings()
        exchange_rate = float(settings.get('coinExchangeRate', 10.0))
        recharge_discount_rules = settings.get('rechargeDiscountRules', [])
        
        print(f'使用配置: exchange_rate={exchange_rate}, discount_rules={recharge_discount_rules}')
        
        # 获取所有充值记录
        recharge_transactions = Transaction.query.filter_by(
            transaction_type='recharge'
        ).order_by(Transaction.created_at.asc()).all()
        
        print(f'找到 {len(recharge_transactions)} 条充值记录')
        
        updated_count = 0
        for trans in recharge_transactions:
            if trans.points_change:
                points_amount = float(trans.points_change)
                
                # 计算实际现金金额
                actual_cash = calculate_recharge_price(points_amount, exchange_rate, recharge_discount_rules)
                
                # 如果actual_cash_amount为空或与计算值不一致，则更新
                if not trans.actual_cash_amount or abs(float(trans.actual_cash_amount) - actual_cash) > 0.01:
                    old_value = float(trans.actual_cash_amount) if trans.actual_cash_amount else 0
                    trans.actual_cash_amount = actual_cash
                    updated_count += 1
                    print(f'更新记录 ID={trans.id}: points={points_amount}, old_cash={old_value}, new_cash={actual_cash}, unit_price={actual_cash/points_amount:.2f}')
        
        if updated_count > 0:
            db.session.commit()
            print(f'成功更新 {updated_count} 条充值记录')
        else:
            print('没有需要更新的记录')
            
    except Exception as e:
        db.session.rollback()
        print(f'错误: {str(e)}')
        import traceback
        traceback.print_exc()

