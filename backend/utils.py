from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import json

def hash_password(password):
    """加密密码"""
    return generate_password_hash(password)

def verify_password(password_hash, password):
    """验证密码"""
    return check_password_hash(password_hash, password)

def hash_pay_password(pay_password):
    """加密支付密码"""
    return generate_password_hash(pay_password)

def verify_pay_password(pay_password_hash, pay_password):
    """验证支付密码"""
    if not pay_password_hash:
        return False
    return check_password_hash(pay_password_hash, pay_password)

def get_base_price(settlement_date, settings=None):
    """根据日期获取基础单价（从系统配置读取）"""
    if isinstance(settlement_date, str):
        settlement_date = datetime.strptime(settlement_date, '%Y-%m-%d').date()
    
    # 从系统配置获取价格（如果未传入settings，则获取）
    if settings is None:
        settings = get_system_settings()
    price_config = settings.get('price', {})
    
    # 0=Monday, 4=Friday
    if settlement_date.weekday() == 4:
        return float(price_config.get('fridayPrice', 1.5))
    return float(price_config.get('basePrice', 1.0))

def get_discount_by_order_count(order_count, discount_rules):
    """根据订单数量获取折扣率"""
    if not discount_rules:
        print(f'[DEBUG] get_discount_by_order_count - 无折扣规则，订单数量: {order_count}，返回1.0（不打折）')
        return 1.0  # 如果没有规则，返回1.0（不打折）
    
    # 按minOrders降序排序，找到最大的适用规则
    applicable_rules = [r for r in discount_rules if order_count >= r['minOrders']]
    print(f'[DEBUG] get_discount_by_order_count - 订单数量: {order_count}, 折扣规则: {discount_rules}, 适用规则: {applicable_rules}')
    
    if not applicable_rules:
        print(f'[DEBUG] get_discount_by_order_count - 无适用规则，返回1.0（不打折）')
        return 1.0  # 如果没有匹配的规则，返回1.0（不打折）
    
    max_rule = max(applicable_rules, key=lambda x: x['minOrders'])
    discount_rate = max_rule['discount']
    print(f'[DEBUG] get_discount_by_order_count - 应用规则: minOrders={max_rule["minOrders"]}, discount={discount_rate}, 最终折扣率: {discount_rate}')
    return discount_rate

def calculate_order_price(base_price, discount_rate, quantity):
    """
    计算订单总价
    规则：数量 * 单价 * 折扣率
    例如：数量3，单价1，折扣0.9（90%），总价 = 3 * 1 * 0.9 = 2.7
    """
    # 计算折扣后的单价（用于显示）
    final_price = base_price * discount_rate
    # 计算总金币：数量 * 单价 * 折扣率
    total_points = quantity * base_price * discount_rate
    # 保留2位小数，避免浮点数精度问题
    return round(float(final_price), 2), round(float(total_points), 2)

def calculate_recharge_price(points_amount, exchange_rate, discount_rules):
    """计算充值所需现金（考虑优惠）"""
    # 确保discount_rules是列表格式
    if not isinstance(discount_rules, list):
        discount_rules = []
    
    # 找到适用的优惠规则（按minAmount降序排序，找到最大的适用规则）
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
        print(f'[DEBUG] calculate_recharge_price: 应用优惠规则 minAmount={applicable_rule.get("minAmount")}, discount={discount}, base_cash={base_cash}, actual_cash={actual_cash}')
    else:
        actual_cash = base_cash
        print(f'[DEBUG] calculate_recharge_price: 无适用优惠规则, base_cash={base_cash}, actual_cash={actual_cash}')
    
    return round(actual_cash, 2)

def calculate_agent_purchase_price(points_amount, exchange_rate, discount_rules):
    """计算代理购买金币的实际单价（元/金币）"""
    actual_cash = calculate_recharge_price(points_amount, exchange_rate, discount_rules)
    if points_amount > 0:
        return round(actual_cash / points_amount, 2)
    return exchange_rate

def get_system_settings():
    """获取系统配置（从数据库或默认值）"""
    from models import SystemSetting, db
    
    default_settings = {
        'contact': {
            'wechat': 'kefu123456',
            'phone': '400-123-4567',
            'qq': '123456789'
        },
        'price': {
            'basePrice': 1.0,
            'fridayPrice': 1.5
        },
        'coinExchangeRate': 10.0,  # 默认10元=1金币
        'discountRules': [],  # 默认无折扣规则，需要后台配置
        'rewardRates': {
            'direct': 0.03,
            'indirect': 0.01
        },
        'transferLimits': {
            'minQuantity': 10,
            'maxUnitPrice': 1.5
        },
        'rechargeDiscountRules': [
            {'minAmount': 200, 'discount': 95},
            {'minAmount': 100, 'discount': 98}
        ]
    }
    
    try:
        # 使用 db.session.query 确保获取最新数据，避免缓存
        from models import SystemSetting
        # 先expire_all()清除可能的缓存，然后查询最新数据
        db.session.expire_all()
        settings_obj = db.session.query(SystemSetting).filter_by(setting_key='system_config').first()
        if settings_obj:
            loaded_settings = json.loads(settings_obj.setting_value)
            # 确保数值类型正确（特别是transferLimits中的数值）
            if 'transferLimits' in loaded_settings:
                transfer_limits = loaded_settings['transferLimits']
                if 'minQuantity' in transfer_limits:
                    transfer_limits['minQuantity'] = float(transfer_limits['minQuantity'])
                if 'maxUnitPrice' in transfer_limits:
                    transfer_limits['maxUnitPrice'] = float(transfer_limits['maxUnitPrice'])
            # 确保coinExchangeRate是float
            if 'coinExchangeRate' in loaded_settings:
                loaded_settings['coinExchangeRate'] = float(loaded_settings['coinExchangeRate'])
            print(f'[DEBUG] 读取系统配置: transferLimits={loaded_settings.get("transferLimits", {})}, coinExchangeRate={loaded_settings.get("coinExchangeRate", 10.0)}')
            return loaded_settings
    except Exception as e:
        print(f'[WARNING] 读取系统配置失败，使用默认值: {str(e)}')
        import traceback
        traceback.print_exc()
        pass
    
    return default_settings

def create_transaction(user_id, transaction_type, points_change, balance, description='', related_user_id=None, unit_price=None, actual_cash_amount=None):
    """创建交易记录"""
    from models import Transaction, db
    transaction = Transaction(
        user_id=user_id,
        transaction_type=transaction_type,
        points_change=points_change,
        balance=balance,
        description=description,
        related_user_id=related_user_id,
        unit_price=unit_price,
        actual_cash_amount=actual_cash_amount
    )
    db.session.add(transaction)
    return transaction
