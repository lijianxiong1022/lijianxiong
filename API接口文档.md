# API接口详细文档

## 基础信息

- **Base URL**: `/api/v1`
- **认证方式**: JWT Bearer Token
- **请求格式**: JSON
- **响应格式**: JSON

## 通用响应格式

### 成功响应
```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2023-06-15T10:30:00Z"
}
```

### 错误响应
```json
{
  "success": false,
  "data": null,
  "message": "错误信息",
  "timestamp": "2023-06-15T10:30:00Z",
  "error_code": "ERROR_CODE"
}
```

## 一、用户端API

### 1.1 用户注册
**POST** `/user/register`

**请求体**:
```json
{
  "name": "张三",
  "phone": "13800138000",
  "password": "123456",
  "promoCode": "123456",
  "payPassword": "123456"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "userId": 1,
    "promoCode": "123456",
    "token": "jwt_token_here"
  }
}
```

### 1.2 用户登录
**POST** `/user/login`

**请求体**:
```json
{
  "phone": "13800138000",
  "password": "123456"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "token": "jwt_token_here",
    "user": {
      "id": 1,
      "name": "张三",
      "phone": "138****8000",
      "userType": "agent",
      "points": 1500
    }
  }
}
```

### 1.3 创建报单
**POST** `/orders`

**请求头**: `Authorization: Bearer {token}`

**请求体**:
```json
{
  "nonMemberIds": [1, 2, 3],
  "settlementDate": "2023-06-15",
  "quantity": 3
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "orderId": 1001,
    "totalPoints": 2.7,
    "remainingPoints": 1497.3
  }
}
```

### 1.4 获取订单列表
**GET** `/orders?page=1&pageSize=20&startDate=2023-06-01&endDate=2023-06-30`

**响应**:
```json
{
  "success": true,
  "data": {
    "list": [
      {
        "id": 1001,
        "settlementDate": "2023-06-15",
        "quantity": 3,
        "totalPoints": 2.7,
        "status": "approved"
      }
    ],
    "total": 50,
    "page": 1,
    "pageSize": 20
  }
}
```

### 1.5 转账金币
**POST** `/points/transfer`

**请求体**:
```json
{
  "toPhone": "13900139000",
  "quantity": 100,
  "unitPrice": 1.2,
  "payPassword": "123456"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "transactionId": 2001,
    "remainingPoints": 1380
  }
}
```

## 二、后台管理API

### 2.1 管理员登录
**POST** `/admin/login`

**请求体**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

### 2.2 获取会员列表
**GET** `/admin/members?page=1&pageSize=20&id=123456&phone=138&date=2023-06-01`

**响应**:
```json
{
  "success": true,
  "data": {
    "list": [
      {
        "id": "123456",
        "name": "张三",
        "phone": "138****1234",
        "type": "普通会员",
        "parentId": "654321",
        "points": 1500,
        "registerDate": "2023-01-15",
        "nonmemberCount": 8,
        "todayOrders": 5,
        "monthOrders": 120
      }
    ],
    "total": 100,
    "page": 1,
    "pageSize": 20
  }
}
```

### 2.3 代理充值
**POST** `/admin/agents/:id/recharge`

**请求体**:
```json
{
  "points": 1000,
  "adminPassword": "admin_password"
}
```

### 2.4 获取系统配置
**GET** `/admin/settings`

**响应**:
```json
{
  "success": true,
  "data": {
    "contact": {
      "wechat": "kefu123456",
      "phone": "400-123-4567",
      "qq": "123456789"
    },
    "price": {
      "basePrice": 1,
      "fridayPrice": 1.5
    },
    "discountRules": [
      { "minOrders": 20, "discount": 0.4 },
      { "minOrders": 10, "discount": 0.25 }
    ],
    "rewardRates": {
      "direct": 3,
      "indirect": 1
    }
  }
}
```

### 2.5 更新系统配置
**PUT** `/admin/settings`

**请求体**:
```json
{
  "contact": {...},
  "price": {...},
  "discountRules": [...],
  "rewardRates": {...}
}
```

## 三、错误码说明

| 错误码 | 说明 |
|--------|------|
| AUTH_FAILED | 认证失败 |
| INVALID_PARAMS | 参数错误 |
| USER_NOT_FOUND | 用户不存在 |
| PROMO_CODE_EXISTS | 推广码已存在 |
| INSUFFICIENT_POINTS | 金币不足 |
| INVALID_PAY_PASSWORD | 支付密码错误 |
| PERMISSION_DENIED | 权限不足 |

