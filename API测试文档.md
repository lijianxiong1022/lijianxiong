# API接口测试文档

## 目录
1. [环境准备](#环境准备)
2. [用户端接口](#用户端接口)
3. [管理员接口](#管理员接口)
4. [测试工具](#测试工具)

---

## 环境准备

### 1. 启动后端服务

```bash
cd backend
python app.py
```

后端服务默认运行在：`http://localhost:5000`

### 2. 初始化数据库

```bash
cd backend
python init_db.py
```

默认管理员账号：
- 用户名：`admin`
- 密码：`admin123`

---

## 用户端接口

### 基础URL
```
http://localhost:5000/api/v1
```

### 1. 用户注册

**接口：** `POST /user/register`

**请求头：**
```
Content-Type: application/json
```

**请求体：**
```json
{
  "name": "张三",
  "phone": "13800138000",
  "password": "123456",
  "payPassword": "123456",
  "promoCode": "123456"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "注册成功",
  "data": {
    "userId": 1,
    "promoCode": "456789",
    "token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

**测试命令（使用curl）：**
```bash
curl -X POST http://localhost:5000/api/v1/user/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "张三",
    "phone": "13800138000",
    "password": "123456",
    "payPassword": "123456",
    "promoCode": "123456"
  }'
```

---

### 2. 用户登录

**接口：** `POST /user/login`

**请求体：**
```json
{
  "phone": "13800138000",
  "password": "123456"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": 1,
      "promoCode": "456789",
      "name": "张三",
      "phone": "138****8000",
      "userType": "ordinary",
      "points": 0.0
    }
  }
}
```

**测试命令：**
```bash
curl -X POST http://localhost:5000/api/v1/user/login \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138000",
    "password": "123456"
  }'
```

---

### 3. 获取用户信息

**接口：** `GET /user/profile`

**请求头：**
```
Authorization: Bearer {token}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "promoCode": "456789",
    "name": "张三",
    "phone": "138****8000",
    "userType": "ordinary",
    "parentId": 2,
    "points": 1000.0,
    "registerDate": "2024-01-15",
    "parent": {
      "name": "李四",
      "phone": "13900139000"
    },
    "agentCount": 0
  }
}
```

**测试命令：**
```bash
curl -X GET http://localhost:5000/api/v1/user/profile \
  -H "Authorization: Bearer {token}"
```

---

### 4. 验证推广码

**接口：** `POST /user/validate-promo-code`

**请求体：**
```json
{
  "promoCode": "123456"
}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "isUnique": true,
    "exists": true
  }
}
```

---

### 5. 获取非会员列表

**接口：** `GET /users/nonmembers`

**请求头：**
```
Authorization: Bearer {token}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "list": [
      {
        "id": 1,
        "name": "非会员A",
        "link": "https://t.cn/R123456",
        "ownerId": 1,
        "createdAt": "2024-01-15 10:30:00"
      }
    ]
  }
}
```

---

### 6. 添加非会员

**接口：** `POST /users/nonmembers`

**请求头：**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**请求体：**
```json
{
  "name": "非会员B",
  "link": "https://t.cn/R789012"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "添加成功",
  "data": {
    "id": 2,
    "name": "非会员B",
    "link": "https://t.cn/R789012",
    "ownerId": 1,
    "createdAt": "2024-01-15 11:00:00"
  }
}
```

---

### 7. 删除非会员

**接口：** `DELETE /users/nonmembers/{id}`

**请求头：**
```
Authorization: Bearer {token}
```

**测试命令：**
```bash
curl -X DELETE http://localhost:5000/api/v1/users/nonmembers/1 \
  -H "Authorization: Bearer {token}"
```

---

### 8. 提交订单（报单）

**接口：** `POST /orders`

**请求头：**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**请求体：**
```json
{
  "nonMemberIds": [1, 2],
  "settlementDate": "2024-01-15",
  "quantity": 1
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "报单成功",
  "data": {
    "orderId": 1,
    "points": 950.0
  }
}
```

---

### 9. 获取订单列表

**接口：** `GET /orders`

**请求头：**
```
Authorization: Bearer {token}
```

**查询参数：**
- `page`: 页码（默认：1）
- `pageSize`: 每页数量（默认：20）
- `startDate`: 开始日期（格式：YYYY-MM-DD）
- `endDate`: 结束日期（格式：YYYY-MM-DD）
- `status`: 订单状态（pending, approved, rejected）

**测试命令：**
```bash
curl -X GET "http://localhost:5000/api/v1/orders?page=1&pageSize=20&startDate=2024-01-01&endDate=2024-01-31" \
  -H "Authorization: Bearer {token}"
```

---

### 10. 获取订单统计

**接口：** `GET /orders/statistics`

**请求头：**
```
Authorization: Bearer {token}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "todayOrderCount": 5,
    "monthOrderCount": 120
  }
}
```

---

### 11. 获取金币余额

**接口：** `GET /points/balance`

**请求头：**
```
Authorization: Bearer {token}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "points": 1000.0
  }
}
```

---

### 12. 转账金币

**接口：** `POST /points/transfer`

**请求头：**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**请求体：**
```json
{
  "toPhone": "13900139000",
  "quantity": 100,
  "unitPrice": 1.2,
  "payPassword": "123456"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "转账成功",
  "data": {
    "points": 880.0,
    "toUserName": "李四"
  }
}
```

---

### 13. 获取交易记录列表

**接口：** `GET /transactions`

**请求头：**
```
Authorization: Bearer {token}
```

**查询参数：**
- `page`: 页码（默认：1）
- `pageSize`: 每页数量（默认：20）
- `transactionType`: 交易类型（recharge, order_deduction, transfer_out, transfer_in, reward）
- `startDate`: 开始日期（格式：YYYY-MM-DD）
- `endDate`: 结束日期（格式：YYYY-MM-DD）

**响应示例：**
```json
{
  "success": true,
  "data": {
    "list": [
      {
        "id": 1,
        "userId": 1,
        "transactionType": "order_deduction",
        "pointsChange": -50.0,
        "balance": 950.0,
        "description": "报单扣除，日期: 2024-01-15, 数量: 1, 单价: 0.60, 折扣: 40%",
        "relatedUserId": null,
        "createdAt": "2024-01-15 10:30:00"
      }
    ],
    "total": 10,
    "page": 1,
    "pageSize": 20
  }
}
```

---

### 14. 获取交易统计

**接口：** `GET /transactions/statistics`

**请求头：**
```
Authorization: Bearer {token}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "today": {
      "recharge": 500.0,
      "orderDeduction": 100.0
    },
    "yesterday": {
      "orderDeduction": 80.0
    },
    "month": {
      "recharge": 2000.0,
      "orderDeduction": 1500.0
    },
    "lastMonth": {
      "orderDeduction": 1200.0
    }
  }
}
```

---

### 15. 获取奖励记录列表

**接口：** `GET /rewards`

**请求头：**
```
Authorization: Bearer {token}
```

**查询参数：**
- `page`: 页码（默认：1）
- `pageSize`: 每页数量（默认：20）
- `rewardType`: 奖励类型（direct, indirect）
- `startDate`: 开始日期（格式：YYYY-MM-DD）
- `endDate`: 结束日期（格式：YYYY-MM-DD）

---

### 16. 获取奖励统计

**接口：** `GET /rewards/statistics`

**请求头：**
```
Authorization: Bearer {token}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "today": {
      "directReward": 15.0,
      "indirectReward": 5.0
    },
    "total": {
      "directReward": 300.0,
      "indirectReward": 100.0
    }
  }
}
```

---

### 17. 升级为代理

**接口：** `POST /users/upgrade-to-agent`

**请求头：**
```
Authorization: Bearer {token}
```

**响应示例：**
```json
{
  "success": true,
  "message": "升级为代理成功",
  "data": {
    "userType": "agent"
  }
}
```

---

## 管理员接口

### 基础URL
```
http://localhost:5000/api/v1
```

### 1. 管理员登录

**接口：** `POST /admin/login`

**请求体：**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": 1,
      "username": "admin",
      "name": "管理员",
      "role": "admin"
    }
  }
}
```

---

### 2. 为用户充值

**接口：** `POST /admin/recharge`

**请求头：**
```
Authorization: Bearer {admin_token}
Content-Type: application/json
```

**请求体：**
```json
{
  "userId": 1,
  "points": 1000,
  "adminPassword": "admin123"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "充值成功",
  "data": {
    "points": 2000.0,
    "rechargeAmount": 1000
  }
}
```

---

### 3. 修改用户支付密码

**接口：** `PUT /admin/users/{userId}/pay-password`

**请求头：**
```
Authorization: Bearer {admin_token}
Content-Type: application/json
```

**请求体：**
```json
{
  "payPassword": "654321"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "支付密码修改成功",
  "data": null
}
```

**测试命令：**
```bash
curl -X PUT http://localhost:5000/api/v1/admin/users/1/pay-password \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "payPassword": "654321"
  }'
```

---

## 测试工具

### 使用Postman测试

1. **创建环境变量**
   - `base_url`: `http://localhost:5000/api/v1`
   - `user_token`: 用户登录后获取的token
   - `admin_token`: 管理员登录后获取的token

2. **设置请求头**
   - 对于需要认证的接口，添加：
     ```
     Authorization: Bearer {{user_token}}
     ```
   - 或
     ```
     Authorization: Bearer {{admin_token}}
     ```

### 使用Python测试脚本

创建 `test_api.py`：

```python
import requests
import json

BASE_URL = "http://localhost:5000/api/v1"

# 1. 用户注册
def test_register():
    url = f"{BASE_URL}/user/register"
    data = {
        "name": "测试用户",
        "phone": "13800138000",
        "password": "123456",
        "payPassword": "123456",
        "promoCode": "123456"  # 需要先有一个上级用户的推广码
    }
    response = requests.post(url, json=data)
    print("注册结果:", response.json())
    return response.json().get('data', {}).get('token')

# 2. 用户登录
def test_login():
    url = f"{BASE_URL}/user/login"
    data = {
        "phone": "13800138000",
        "password": "123456"
    }
    response = requests.post(url, json=data)
    print("登录结果:", response.json())
    return response.json().get('data', {}).get('token')

# 3. 获取用户信息
def test_get_profile(token):
    url = f"{BASE_URL}/user/profile"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    print("用户信息:", response.json())

# 4. 添加非会员
def test_add_nonmember(token):
    url = f"{BASE_URL}/users/nonmembers"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "name": "测试非会员",
        "link": "https://t.cn/R123456"
    }
    response = requests.post(url, json=data, headers=headers)
    print("添加非会员结果:", response.json())

# 5. 提交订单
def test_submit_order(token):
    url = f"{BASE_URL}/orders"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "nonMemberIds": [1],
        "settlementDate": "2024-01-15",
        "quantity": 1
    }
    response = requests.post(url, json=data, headers=headers)
    print("提交订单结果:", response.json())

# 6. 获取交易记录
def test_get_transactions(token):
    url = f"{BASE_URL}/transactions"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "page": 1,
        "pageSize": 20
    }
    response = requests.get(url, headers=headers, params=params)
    print("交易记录:", response.json())

# 7. 管理员登录
def test_admin_login():
    url = f"{BASE_URL}/admin/login"
    data = {
        "username": "admin",
        "password": "admin123"
    }
    response = requests.post(url, json=data)
    print("管理员登录结果:", response.json())
    return response.json().get('data', {}).get('token')

# 8. 管理员充值
def test_admin_recharge(admin_token):
    url = f"{BASE_URL}/admin/recharge"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    data = {
        "userId": 1,
        "points": 1000,
        "adminPassword": "admin123"
    }
    response = requests.post(url, json=data, headers=headers)
    print("充值结果:", response.json())

if __name__ == "__main__":
    # 测试流程
    print("=== 开始测试 ===")
    
    # 1. 用户登录
    token = test_login()
    if not token:
        print("登录失败，请先注册用户")
        exit(1)
    
    # 2. 获取用户信息
    test_get_profile(token)
    
    # 3. 添加非会员
    test_add_nonmember(token)
    
    # 4. 提交订单
    test_submit_order(token)
    
    # 5. 获取交易记录
    test_get_transactions(token)
    
    # 6. 管理员登录
    admin_token = test_admin_login()
    
    # 7. 管理员充值
    if admin_token:
        test_admin_recharge(admin_token)
    
    print("=== 测试完成 ===")
```

---

## 错误码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（Token无效或过期） |
| 403 | 权限不足（需要管理员权限） |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 注意事项

1. **Token有效期**：Token默认有效期为24小时，过期后需要重新登录
2. **推广码**：注册时必须填写有效的上级推广码（6位数字）
3. **支付密码**：必须是6位数字
4. **转账限制**：
   - 最低转账数量：10（可在后台配置）
   - 最高转账单价：1.5元/金币（可在后台配置）
5. **订单日期**：不能选择今天之前的日期
6. **金币精度**：所有金币相关数值保留2位小数

---

## 测试检查清单

### 用户端功能
- [ ] 用户注册（需要上级推广码）
- [ ] 用户登录
- [ ] 获取用户信息（包含上级信息和代理人数）
- [ ] 添加非会员（检查重复名称和链接）
- [ ] 删除非会员
- [ ] 提交订单（检查金币余额）
- [ ] 获取订单列表（支持日期和状态筛选）
- [ ] 获取订单统计
- [ ] 获取金币余额
- [ ] 转账金币（检查支付密码、转账限制）
- [ ] 获取交易记录（支持类型和日期筛选）
- [ ] 获取交易统计
- [ ] 获取奖励记录
- [ ] 获取奖励统计
- [ ] 升级为代理

### 管理员功能
- [ ] 管理员登录
- [ ] 为用户充值（需要管理员密码）
- [ ] 修改用户支付密码

---

## 常见问题

### 1. Token无效或过期
**解决方法：** 重新登录获取新的Token

### 2. 推广码不存在
**解决方法：** 确保使用有效的6位数字推广码，该推广码必须是已注册用户的推广码

### 3. 金币不足
**解决方法：** 检查用户金币余额，或通过管理员充值

### 4. 支付密码错误
**解决方法：** 确认支付密码为6位数字，或通过管理员重置

### 5. 转账限制
**解决方法：** 检查转账数量和单价是否符合后台配置的限制

---

## 更新日志

### 2024-01-15
- ✅ 完成所有用户端接口
- ✅ 完成管理员接口
- ✅ 添加交易记录查询和统计
- ✅ 添加奖励记录和统计
- ✅ 添加订单统计
- ✅ 添加转账功能
- ✅ 添加充值功能
- ✅ 添加修改支付密码功能

