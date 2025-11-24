#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""根据优惠规则修复充值记录的actual_cash_amount"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import create_app
from models import db, Transaction
from utils import calculate_recharge_price

# 定义优惠规则（根据后台配置）
# 充值100以上98折，充值200以上95折
DISCOUNT_RULES = [
    {'minAmount': 200, 'discount': 95},  # 充值200以上95折
    {'minAmount': 100, 'discount': 98}   # 充值100以上98折
]
EXCHANGE_RATE = 10.0  # 10元=1金币

app = create_app()
with app.app_context():
    try:
        # 获取所有充值记录
        recharge_transactions = Transaction.query.filter_by(
            transaction_type='recharge'
        ).order_by(Transaction.created_at.asc()).all()
        
        print(f'找到 {len(recharge_transactions)} 条充值记录')
        
        updated_count = 0
        for trans in recharge_transactions:
            if trans.points_change:
                points_amount = float(trans.points_change)
                
                # 计算实际现金金额（应用优惠规则）
                actual_cash = calculate_recharge_price(points_amount, EXCHANGE_RATE, DISCOUNT_RULES)
                
                # 如果actual_cash_amount与计算值不一致，则更新
                current_cash = float(trans.actual_cash_amount) if trans.actual_cash_amount else 0
                if abs(current_cash - actual_cash) > 0.01:
                    trans.actual_cash_amount = actual_cash
                    updated_count += 1
                    unit_price = actual_cash / points_amount if points_amount > 0 else 0
                    print(f'更新记录 ID={trans.id}: points={points_amount}, old_cash={current_cash:.2f}, new_cash={actual_cash:.2f}, unit_price={unit_price:.2f}')
        
        if updated_count > 0:
            db.session.commit()
            print(f'\n成功更新 {updated_count} 条充值记录')
        else:
            print('没有需要更新的记录')
            
    except Exception as e:
        db.session.rollback()
        print(f'错误: {str(e)}')
        import traceback
        traceback.print_exc()

