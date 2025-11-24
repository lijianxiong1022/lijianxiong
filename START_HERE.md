# 🚀 开始使用 - 三步启动后端服务

## 📦 当前状态
- ✅ Python环境：已安装
- ✅ 依赖包：已安装
- ⏳ 配置文件：需要创建
- ⏳ 数据库：需要创建和初始化

## 🎯 快速开始（3步）

### 步骤1：创建配置文件

在 `backend` 目录下创建 `.env` 文件（注意文件名是 `.env`，不是 `env`）

**Windows用户**：可以使用记事本创建，文件名输入 `.env`（包含点）

**文件内容**：
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=order_system

JWT_SECRET_KEY=dev-secret-key-2023
JWT_ACCESS_TOKEN_EXPIRES=86400

FLASK_ENV=development
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

**重要**：
- 如果MySQL没有密码，`DB_PASSWORD=` 后面留空
- 如果有密码，填写你的MySQL root密码

### 步骤2：创建并初始化数据库

**方法A：使用一键启动脚本（推荐）**
```bash
cd backend
一键启动.bat
```
脚本会自动检查并初始化数据库

**方法B：手动执行**
```bash
# 1. 创建数据库（在MySQL中执行）
mysql -u root -p
CREATE DATABASE order_system DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;

# 2. 初始化数据库（在backend目录下）
cd backend
python init_db.py
```

### 步骤3：启动服务

```bash
cd backend
python app.py
```

看到以下输出说明成功：
```
 * Running on http://0.0.0.0:5000
```

## 🧪 测试服务

### 方法1：使用浏览器
访问：`http://localhost:5000/api/v1/user/register`
如果看到JSON响应，说明服务正常

### 方法2：使用curl测试注册
```bash
curl -X POST http://localhost:5000/api/v1/user/register -H "Content-Type: application/json" -d "{\"name\":\"测试\",\"phone\":\"13800138000\",\"password\":\"123456\",\"payPassword\":\"123456\"}"
```

## 📋 完整检查清单

启动前请确认：
- [ ] `.env` 文件已创建（在backend目录下）
- [ ] `.env` 中的数据库配置正确
- [ ] MySQL服务已启动
- [ ] 数据库 `order_system` 已创建
- [ ] 已运行 `python init_db.py` 初始化数据库表

## 🆘 常见问题

### Q1: 找不到.env文件？
**A**: 确保文件名是 `.env`（以点开头），不是 `env.txt` 或 `env`

### Q2: MySQL连接失败？
**A**: 
1. 检查MySQL服务是否运行
2. 检查 `.env` 中的用户名密码是否正确
3. 测试连接：`mysql -u root -p`

### Q3: 端口5000被占用？
**A**: 修改 `.env` 中的 `FLASK_PORT=5001`（或其他端口）

### Q4: 模块导入错误？
**A**: 重新安装依赖 `pip install -r requirements.txt`

## 🎉 成功标志

如果看到：
```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

恭喜！后端服务已成功启动！

## 📞 需要帮助？

如果遇到问题：
1. 查看 `backend/README.md` 详细文档
2. 查看 `快速开始.md` 完整指南
3. 运行 `python check_setup.py` 检查环境

---

**提示**：如果MySQL没有安装，我可以帮你改用SQLite（更简单，无需安装数据库）

