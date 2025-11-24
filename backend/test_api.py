"""测试API接口"""
import urllib.request
import urllib.parse
import json

BASE_URL = "http://localhost:5000/api/v1"

def test_register():
    """测试用户注册"""
    url = f"{BASE_URL}/user/register"
    data = {
        "name": "测试用户",
        "phone": "13800138000",
        "password": "123456",
        "payPassword": "123456"
    }
    try:
        req = urllib.request.Request(url, 
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"注册接口测试:")
            print(f"  状态码: {response.status}")
            print(f"  响应: {result}")
            return response.status == 200
    except urllib.error.HTTPError as e:
        result = json.loads(e.read().decode('utf-8'))
        print(f"注册接口测试:")
        print(f"  状态码: {e.code}")
        print(f"  响应: {result}")
        return False
    except Exception as e:
        print(f"注册接口测试失败: {e}")
        return False

def test_login():
    """测试用户登录"""
    url = f"{BASE_URL}/user/login"
    data = {
        "phone": "13800138000",
        "password": "123456"
    }
    try:
        req = urllib.request.Request(url, 
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"\n登录接口测试:")
            print(f"  状态码: {response.status}")
            print(f"  响应: {result}")
            return response.status == 200
    except urllib.error.HTTPError as e:
        result = json.loads(e.read().decode('utf-8'))
        print(f"\n登录接口测试:")
        print(f"  状态码: {e.code}")
        print(f"  响应: {result}")
        return False
    except Exception as e:
        print(f"登录接口测试失败: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("API接口测试")
    print("=" * 50)
    
    # 测试注册
    register_ok = test_register()
    
    # 测试登录
    if register_ok:
        login_ok = test_login()
    
    print("\n" + "=" * 50)
    if register_ok:
        print("[OK] 服务运行正常！")
    else:
        print("[ERROR] 服务测试失败")

