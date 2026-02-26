# 健康管理系统

一个基于Vue.js和FastAPI的现代化健康管理系统，支持健康数据记录、AI健康助手、知识中心等功能。

## 功能特性

- 🔐 **用户认证**: 支持用户注册、登录、权限管理
- 📊 **健康数据管理**: 记录和分析体重、血压、心率、血糖等健康指标
- 🤖 **AI健康助手**: 智能健康问答和个性化建议
- 📚 **健康知识中心**: 健康知识浏览和学习
- 📱 **响应式设计**: 支持桌面端和移动端

## 技术栈

### 后端
- **FastAPI**: 现代化的Python Web框架
- **SQLAlchemy**: ORM数据库操作
- **MySQL**: 关系型数据库
- **JWT**: 用户认证
- **Pydantic**: 数据验证

### 前端
- **Vue 3**: 现代化前端框架
- **Element Plus**: UI组件库
- **Axios**: HTTP客户端
- **Vue Router**: 路由管理

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- MySQL 8.0+

### 后端启动

1. 进入后端目录
```bash
cd backend
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置数据库
```bash
# 修改 app/config.py 中的数据库配置
# 或设置环境变量
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=your_password
export DB_NAME=health
```

5. 启动服务
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端启动

1. 进入前端目录
```bash
cd frontend
```

2. 安装依赖
```bash
npm install
```

3. 启动开发服务器
```bash
npm run dev
```

4. 访问应用
```
http://localhost:3000
```

## 默认账号

系统会自动创建以下测试账号：

### 管理员账号
- 用户名: `admin`
- 密码: `admin123`
- 邮箱: `admin@health.com`

### 普通用户账号
- 用户名: `xiaoming`
- 密码: `123456`
- 邮箱: `xiaoming@health.com`

- 用户名: `xiaohong`
- 密码: `123456`
- 邮箱: `xiaohong@health.com`

## API文档

后端启动后，可以访问以下地址查看API文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 项目结构

```
健康管理系统/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── models.py       # 数据模型
│   │   ├── schemas.py      # 数据验证
│   │   ├── main.py         # 应用入口
│   │   ├── config.py       # 配置文件
│   │   ├── database.py     # 数据库配置
│   │   ├── routers/        # API路由
│   │   └── services/       # 业务逻辑
│   └── requirements.txt     # Python依赖
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── api/            # API调用
│   │   ├── components/      # 公共组件
│   │   └── router/         # 路由配置
│   └── package.json        # Node.js依赖
└── contracts/              # 智能合约（未来扩展）
```

## 功能说明

### 1. 用户认证
- 用户注册和登录
- JWT令牌认证
- 角色权限管理（管理员/普通用户）

### 2. 健康数据管理
- 记录体重、血压、心率、血糖等数据
- 数据可视化展示
- 健康趋势分析
- 数据导出功能

### 3. AI健康助手
- 智能健康问答
- 个性化健康建议
- 基于健康数据的分析
- 对话历史记录

### 4. 健康知识中心
- 健康知识文章浏览
- 分类检索功能
- 内容搜索
- 收藏和分享

## 开发计划

- [ ] 大模型集成（GPT等）
- [ ] 区块链数据存储
- [ ] 移动端APP
- [ ] 数据可视化图表
- [ ] 健康报告生成
- [ ] 提醒通知功能

## 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 邮箱: health@example.com
- 项目地址: https://github.com/your-username/health-management-system

---

**注意**: 这是一个演示项目，生产环境使用前请进行充分的安全测试和性能优化。
