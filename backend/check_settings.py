#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查系统配置"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import create_app
from models import db, SystemSetting
import json

app = create_app()
with app.app_context():
    setting = SystemSetting.query.filter_by(setting_key='system_config').first()
    if setting:
        settings = json.loads(setting.setting_value)
        print(f'coinExchangeRate: {settings.get("coinExchangeRate", "未设置")}')
        print(f'rechargeDiscountRules: {settings.get("rechargeDiscountRules", [])}')
    else:
        print('未找到系统配置')

