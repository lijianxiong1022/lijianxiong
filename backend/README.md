# 报单系统后端API

## 技术栈
- Python 3.8+
- Flask 2.3.3
- SQLAlchemy (ORM)
- PyMySQL (MySQL驱动)
- Flask-JWT-Extended (JWT认证)
- Flask-CORS (跨域支持)

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接信息
```

### 3. 创建数据库
```bash
mysql -u root -p < ../database/init.sql
```

### 4. 初始化数据库
```bash
python init_db.py
```

### 5. 启动服务
```bash
python app.py
```

服务将在 `http://localhost:5000` 启动

## API接口

### 用户端接口

#### 用户注册
```
POST /api/v1/user/register
Content-Type: application/json

{
  "name": "张三",
  "phone": "13800138000",
  "password": "123456",
  "promoCode": "123456",  // 可选，上级推广码
  "payPassword": "123456"
}
```

#### 用户登录
```
POST /api/v1/user/login
Content-Type: application/json

{
  "phone": "13800138000",
  "password": "123456"
}
```

#### 创建报单
```
POST /api/v1/orders
Authorization: Bearer {token}
Content-Type: application/json

{
  "nonMemberIds": [1, 2, 3],
  "settlementDate": "2023-06-15",
  "quantity": 3
}
```

#### 获取订单列表
```
GET /api/v1/orders?page=1&pageSize=20&startDate=2023-06-01&endDate=2023-06-30
Authorization: Bearer {token}
```

#### 获取非会员列表
```
GET /api/v1/users/nonmembers
Authorization: Bearer {token}
```

#### 添加非会员
```
POST /api/v1/users/nonmembers
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "非会员A",
  "link": "https://t.cn/R123456"
}
```

### 管理员接口

#### 管理员登录
```
POST /api/v1/admin/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

## 测试

### 使用curl测试

```bash
# 用户注册
curl -X POST http://localhost:5000/api/v1/user/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试用户",
    "phone": "13800138000",
    "password": "123456",
    "payPassword": "123456"
  }'

# 用户登录
curl -X POST http://localhost:5000/api/v1/user/login \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138000",
    "password": "123456"
  }'

# 获取用户信息（需要Token）
curl -X GET http://localhost:5000/api/v1/user/profile \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 项目结构

```
backend/
├── app.py              # 应用入口
├── config.py           # 配置文件
├── models.py           # 数据模型
├── utils.py            # 工具函数
├── requirements.txt    # 依赖列表
├── .env.example        # 环境变量示例
├── init_db.py          # 数据库初始化脚本
├── api/                # API路由
│   ├── __init__.py
│   ├── auth.py         # 认证相关
│   ├── orders.py       # 订单相关
│   └── users.py        # 用户相关
└── README.md
```

## 注意事项

1. **生产环境配置**
   - 修改 `.env` 中的 `JWT_SECRET_KEY` 为强随机字符串
   - 设置 `FLASK_DEBUG=False`
   - 使用生产级数据库配置

2. **数据库备份**
   - 定期备份数据库
   - 建议使用 `mysqldump` 或云数据库自动备份

3. **安全建议**
   - 使用HTTPS
   - 设置CORS白名单
   - 实施API限流
   - 记录操作日志

## 开发计划

- [x] 用户注册/登录
- [x] 报单功能
- [ ] 金币转账
- [ ] 奖励系统
- [ ] 后台管理API
- [ ] 数据统计
- [ ] 系统配置管理

