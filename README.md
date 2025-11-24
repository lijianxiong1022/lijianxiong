# 私域报单系统

## 项目简介
一个完整的报单管理系统，支持用户注册、报单、金币转账、奖励统计等功能。

## 技术栈
- **后端**: Flask + SQLAlchemy + MySQL/SQLite
- **前端**: HTML + JavaScript + CSS
- **认证**: JWT Token
- **部署**: Systemd + Nginx

## 快速开始

### 本地开发
1. 配置 `.env` 文件（使用SQLite）
2. 运行 `python backend/app.py`
3. 访问 `http://localhost:5000`

### 生产部署
详见 `部署指南.md`

## 项目结构
```
├── backend/          # 后端代码
├── all_pages.html    # 用户端页面
├── admin.html        # 后台管理页面
├── user_api.js       # 用户端API
├── api.js            # 后台API
└── nginx/            # Nginx配置
```

## 部署说明
- 本地开发：使用SQLite数据库
- 生产环境：使用MySQL数据库
- 前端API地址自动检测环境

