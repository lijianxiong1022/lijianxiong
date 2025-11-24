#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API接口测试脚本
使用方法：python test_api.py
"""

import requests
import json
import sys

# 配置
BASE_URL = "http://localhost:5000/api/v1"

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

def test_register():
    """测试用户注册"""
    print_info("测试用户注册...")
    url = f"{BASE_URL}/user/register"
    data = {
        "name": "测试用户A",
        "phone": "13800138001",
        "password": "123456",
        "payPassword": "123456",
        "promoCode": "123456"  # 需要先有一个上级用户的推广码
    }
    try:
        response = requests.post(url, json=data, timeout=5)
        result = response.json()
        if result.get('success'):
            print_success(f"注册成功: {result.get('message')}")
            return result.get('data', {}).get('token')
        else:
            print_error(f"注册失败: {result.get('message')}")
            return None
    except requests.exceptions.ConnectionError:
        print_error("无法连接到服务器，请确保后端服务已启动")
        return None
    except Exception as e:
        print_error(f"注册异常: {str(e)}")
        return None

def test_login(phone="13800138001", password="123456"):
    """测试用户登录"""
    print_info(f"测试用户登录 (手机号: {phone})...")
    url = f"{BASE_URL}/user/login"
    data = {
        "phone": phone,
        "password": password
    }
    try:
        response = requests.post(url, json=data, timeout=5)
        result = response.json()
        if result.get('success'):
            print_success(f"登录成功: {result.get('message')}")
            token = result.get('data', {}).get('token')
            user = result.get('data', {}).get('user', {})
            print_info(f"  用户ID: {user.get('id')}")
            print_info(f"  推广码: {user.get('promoCode')}")
            print_info(f"  用户类型: {user.get('userType')}")
            return token
        else:
            print_error(f"登录失败: {result.get('message')}")
            return None
    except Exception as e:
        print_error(f"登录异常: {str(e)}")
        return None

def test_get_profile(token):
    """测试获取用户信息"""
    print_info("测试获取用户信息...")
    url = f"{BASE_URL}/user/profile"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        result = response.json()
        if result.get('success'):
            print_success("获取用户信息成功")
            user = result.get('data', {})
            print_info(f"  姓名: {user.get('name')}")
            print_info(f"  推广码: {user.get('promoCode')}")
            print_info(f"  用户类型: {user.get('userType')}")
            print_info(f"  金币余额: {user.get('points')}")
            if user.get('parent'):
                print_info(f"  上级: {user.get('parent').get('name')} ({user.get('parent').get('phone')})")
            if user.get('agentCount') is not None:
                print_info(f"  代理人数: {user.get('agentCount')}")
            return True
        else:
            print_error(f"获取用户信息失败: {result.get('message')}")
            return False
    except Exception as e:
        print_error(f"获取用户信息异常: {str(e)}")
        return False

def test_add_nonmember(token):
    """测试添加非会员"""
    print_info("测试添加非会员...")
    url = f"{BASE_URL}/users/nonmembers"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "name": "测试非会员",
        "link": "https://t.cn/R123456"
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=5)
        result = response.json()
        if result.get('success'):
            print_success(f"添加非会员成功: {result.get('message')}")
            return result.get('data', {}).get('id')
        else:
            print_error(f"添加非会员失败: {result.get('message')}")
            return None
    except Exception as e:
        print_error(f"添加非会员异常: {str(e)}")
        return None

def test_get_nonmembers(token):
    """测试获取非会员列表"""
    print_info("测试获取非会员列表...")
    url = f"{BASE_URL}/users/nonmembers"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        result = response.json()
        if result.get('success'):
            count = len(result.get('data', {}).get('list', []))
            print_success(f"获取非会员列表成功，共 {count} 条")
            return True
        else:
            print_error(f"获取非会员列表失败: {result.get('message')}")
            return False
    except Exception as e:
        print_error(f"获取非会员列表异常: {str(e)}")
        return False

def test_submit_order(token, non_member_ids=[1], settlement_date="2024-01-15", quantity=1):
    """测试提交订单"""
    print_info("测试提交订单...")
    url = f"{BASE_URL}/orders"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "nonMemberIds": non_member_ids,
        "settlementDate": settlement_date,
        "quantity": quantity
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=5)
        result = response.json()
        if result.get('success'):
            print_success(f"提交订单成功: {result.get('message')}")
            order_data = result.get('data', {})
            if 'points' in order_data:
                print_info(f"  剩余金币: {order_data.get('points')}")
            return True
        else:
            print_error(f"提交订单失败: {result.get('message')}")
            return False
    except Exception as e:
        print_error(f"提交订单异常: {str(e)}")
        return False

def test_get_orders(token):
    """测试获取订单列表"""
    print_info("测试获取订单列表...")
    url = f"{BASE_URL}/orders"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "page": 1,
        "pageSize": 20
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        result = response.json()
        if result.get('success'):
            count = result.get('data', {}).get('total', 0)
            print_success(f"获取订单列表成功，共 {count} 条")
            return True
        else:
            print_error(f"获取订单列表失败: {result.get('message')}")
            return False
    except Exception as e:
        print_error(f"获取订单列表异常: {str(e)}")
        return False

def test_get_order_statistics(token):
    """测试获取订单统计"""
    print_info("测试获取订单统计...")
    url = f"{BASE_URL}/orders/statistics"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        result = response.json()
        if result.get('success'):
            stats = result.get('data', {})
            print_success("获取订单统计成功")
            print_info(f"  今日报单数: {stats.get('todayOrderCount')}")
            print_info(f"  本月报单数: {stats.get('monthOrderCount')}")
            return True
        else:
            print_error(f"获取订单统计失败: {result.get('message')}")
            return False
    except Exception as e:
        print_error(f"获取订单统计异常: {str(e)}")
        return False

def test_get_points_balance(token):
    """测试获取金币余额"""
    print_info("测试获取金币余额...")
    url = f"{BASE_URL}/points/balance"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        result = response.json()
        if result.get('success'):
            points = result.get('data', {}).get('points', 0)
            print_success(f"获取金币余额成功: {points}")
            return True
        else:
            print_error(f"获取金币余额失败: {result.get('message')}")
            return False
    except Exception as e:
        print_error(f"获取金币余额异常: {str(e)}")
        return False

def test_transfer_points(token, to_phone="13900139000", quantity=10, unit_price=1.2, pay_password="123456"):
    """测试转账"""
    print_info("测试转账...")
    url = f"{BASE_URL}/points/transfer"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "toPhone": to_phone,
        "quantity": quantity,
        "unitPrice": unit_price,
        "payPassword": pay_password
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=5)
        result = response.json()
        if result.get('success'):
            print_success(f"转账成功: {result.get('message')}")
            transfer_data = result.get('data', {})
            if 'points' in transfer_data:
                print_info(f"  剩余金币: {transfer_data.get('points')}")
            return True
        else:
            print_error(f"转账失败: {result.get('message')}")
            return False
    except Exception as e:
        print_error(f"转账异常: {str(e)}")
        return False

def test_get_transactions(token):
    """测试获取交易记录"""
    print_info("测试获取交易记录...")
    url = f"{BASE_URL}/transactions"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "page": 1,
        "pageSize": 20
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        result = response.json()
        if result.get('success'):
            count = result.get('data', {}).get('total', 0)
            print_success(f"获取交易记录成功，共 {count} 条")
            return True
        else:
            print_error(f"获取交易记录失败: {result.get('message')}")
            return False
    except Exception as e:
        print_error(f"获取交易记录异常: {str(e)}")
        return False

def test_get_transaction_statistics(token):
    """测试获取交易统计"""
    print_info("测试获取交易统计...")
    url = f"{BASE_URL}/transactions/statistics"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        result = response.json()
        if result.get('success'):
            stats = result.get('data', {})
            print_success("获取交易统计成功")
            print_info(f"  今日充值: {stats.get('today', {}).get('recharge', 0)}")
            print_info(f"  今日消耗: {stats.get('today', {}).get('orderDeduction', 0)}")
            print_info(f"  本月充值: {stats.get('month', {}).get('recharge', 0)}")
            print_info(f"  本月消耗: {stats.get('month', {}).get('orderDeduction', 0)}")
            return True
        else:
            print_error(f"获取交易统计失败: {result.get('message')}")
            return False
    except Exception as e:
        print_error(f"获取交易统计异常: {str(e)}")
        return False

def test_get_rewards(token):
    """测试获取奖励记录"""
    print_info("测试获取奖励记录...")
    url = f"{BASE_URL}/rewards"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "page": 1,
        "pageSize": 20
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        result = response.json()
        if result.get('success'):
            count = result.get('data', {}).get('total', 0)
            print_success(f"获取奖励记录成功，共 {count} 条")
            return True
        else:
            print_error(f"获取奖励记录失败: {result.get('message')}")
            return False
    except Exception as e:
        print_error(f"获取奖励记录异常: {str(e)}")
        return False

def test_get_reward_statistics(token):
    """测试获取奖励统计"""
    print_info("测试获取奖励统计...")
    url = f"{BASE_URL}/rewards/statistics"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        result = response.json()
        if result.get('success'):
            stats = result.get('data', {})
            print_success("获取奖励统计成功")
            print_info(f"  今日直推奖励: {stats.get('today', {}).get('directReward', 0)}")
            print_info(f"  今日间推奖励: {stats.get('today', {}).get('indirectReward', 0)}")
            print_info(f"  总直推奖励: {stats.get('total', {}).get('directReward', 0)}")
            print_info(f"  总间推奖励: {stats.get('total', {}).get('indirectReward', 0)}")
            return True
        else:
            print_error(f"获取奖励统计失败: {result.get('message')}")
            return False
    except Exception as e:
        print_error(f"获取奖励统计异常: {str(e)}")
        return False

def test_upgrade_to_agent(token):
    """测试升级为代理"""
    print_info("测试升级为代理...")
    url = f"{BASE_URL}/users/upgrade-to-agent"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.post(url, headers=headers, timeout=5)
        result = response.json()
        if result.get('success'):
            print_success(f"升级为代理成功: {result.get('message')}")
            return True
        else:
            print_warning(f"升级为代理失败: {result.get('message')} (可能已经是代理)")
            return False
    except Exception as e:
        print_error(f"升级为代理异常: {str(e)}")
        return False

def test_admin_login(username="admin", password="admin123"):
    """测试管理员登录"""
    print_info(f"测试管理员登录 (用户名: {username})...")
    url = f"{BASE_URL}/admin/login"
    data = {
        "username": username,
        "password": password
    }
    try:
        response = requests.post(url, json=data, timeout=5)
        result = response.json()
        if result.get('success'):
            print_success(f"管理员登录成功: {result.get('message')}")
            admin_data = result.get('data', {}).get('user', {})
            print_info(f"  管理员ID: {admin_data.get('id')}")
            print_info(f"  管理员姓名: {admin_data.get('name')}")
            return result.get('data', {}).get('token')
        else:
            print_error(f"管理员登录失败: {result.get('message')}")
            return None
    except Exception as e:
        print_error(f"管理员登录异常: {str(e)}")
        return None

def test_admin_recharge(admin_token, user_id=1, points=1000, admin_password="admin123"):
    """测试管理员充值"""
    print_info(f"测试管理员充值 (用户ID: {user_id}, 金额: {points})...")
    url = f"{BASE_URL}/admin/recharge"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    data = {
        "userId": user_id,
        "points": points,
        "adminPassword": admin_password
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=5)
        result = response.json()
        if result.get('success'):
            print_success(f"充值成功: {result.get('message')}")
            recharge_data = result.get('data', {})
            if 'points' in recharge_data:
                print_info(f"  用户当前金币: {recharge_data.get('points')}")
            return True
        else:
            print_error(f"充值失败: {result.get('message')}")
            return False
    except Exception as e:
        print_error(f"充值异常: {str(e)}")
        return False

def test_admin_update_pay_password(admin_token, user_id=1, new_pay_password="654321"):
    """测试管理员修改用户支付密码"""
    print_info(f"测试管理员修改用户支付密码 (用户ID: {user_id})...")
    url = f"{BASE_URL}/admin/users/{user_id}/pay-password"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    data = {
        "payPassword": new_pay_password
    }
    try:
        response = requests.put(url, json=data, headers=headers, timeout=5)
        result = response.json()
        if result.get('success'):
            print_success(f"修改支付密码成功: {result.get('message')}")
            return True
        else:
            print_error(f"修改支付密码失败: {result.get('message')}")
            return False
    except Exception as e:
        print_error(f"修改支付密码异常: {str(e)}")
        return False

def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("API接口测试脚本")
    print("="*60 + "\n")
    
    # 检查服务器连接
    print_info("检查服务器连接...")
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}", timeout=3)
        print_success("服务器连接正常")
    except:
        print_error("无法连接到服务器，请确保后端服务已启动 (python app.py)")
        print_warning("提示: 后端服务应运行在 http://localhost:5000")
        return
    
    print("\n" + "-"*60)
    print("用户端接口测试")
    print("-"*60 + "\n")
    
    # 1. 用户登录（使用已存在的账号）
    token = test_login()
    if not token:
        print_warning("登录失败，尝试注册新用户...")
        # 尝试注册（需要先有一个上级用户）
        token = test_register()
        if not token:
            print_error("无法继续测试，请先手动创建一个用户")
            return
    
    if not token:
        return
    
    # 2. 获取用户信息
    test_get_profile(token)
    print()
    
    # 3. 获取非会员列表
    test_get_nonmembers(token)
    print()
    
    # 4. 添加非会员
    nonmember_id = test_add_nonmember(token)
    print()
    
    # 5. 获取金币余额
    test_get_points_balance(token)
    print()
    
    # 6. 获取订单列表
    test_get_orders(token)
    print()
    
    # 7. 获取订单统计
    test_get_order_statistics(token)
    print()
    
    # 8. 获取交易记录
    test_get_transactions(token)
    print()
    
    # 9. 获取交易统计
    test_get_transaction_statistics(token)
    print()
    
    # 10. 获取奖励记录
    test_get_rewards(token)
    print()
    
    # 11. 获取奖励统计
    test_get_reward_statistics(token)
    print()
    
    # 12. 升级为代理（如果还不是代理）
    test_upgrade_to_agent(token)
    print()
    
    print("\n" + "-"*60)
    print("管理员接口测试")
    print("-"*60 + "\n")
    
    # 13. 管理员登录
    admin_token = test_admin_login()
    if admin_token:
        print()
        
        # 14. 管理员充值
        test_admin_recharge(admin_token)
        print()
        
        # 15. 管理员修改支付密码
        test_admin_update_pay_password(admin_token)
        print()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60 + "\n")
    
    print_info("提示：")
    print("  - 如需测试提交订单，请确保有足够的金币余额")
    print("  - 如需测试转账，请确保有收款人用户")
    print("  - 详细接口文档请查看 API测试文档.md")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(0)
    except Exception as e:
        print_error(f"测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

