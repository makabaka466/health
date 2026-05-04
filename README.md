# 健康管理系统

基于 **Vue 3 + FastAPI + MySQL + Web3 + Ollama + Qdrant** 的健康管理平台，覆盖用户档案、健康数据管理、知识库检索、AI 助手、链上存证与管理端系统设置。

## 本次整体审查结论（已处理）

本次已修复一批“明显上下文不匹配/乱码”问题，重点如下：

1. 后端接口报错与日志中的乱码/占位符（`????`）
- 修复文件：`backend/app/controller/health_data_controller.py`
- 结果：更新/授权/共享查看等关键流程的错误提示和日志可读。

2. 区块链服务中的错误提示乱码
- 修复文件：`backend/app/service/blockchain_service.py`
- 结果：`bytes32` 长度校验异常信息恢复为清晰英文。

3. 管理员相关日志与重置密码返回文案乱码
- 修复文件：`backend/app/controller/auth_controller.py`
- 结果：管理员登录、状态修改、重置密码日志与接口返回文案恢复正常。

4. 健康数据页面授权区域大量占位符（`??`）
- 修复文件：`frontend/src/views/HealthData.vue`
- 结果：授权弹窗标题、字段名、表头、按钮文案、演示医生数据、提示信息均可读。

5. 注册页样式注释异常字符
- 修复文件：`frontend/src/views/Register.vue`
- 结果：清理私有区乱码字符。

6. 后端入口文案与注释整理
- 修复文件：`backend/app/main.py`
- 结果：统一 API 标题/描述/根路由文案，去掉重复注释。

---

## 当前代码结构（按实际项目）

```text
健康管理系统/
├─ backend/
│  ├─ app/
│  │  ├─ main.py                      # FastAPI 入口（当前挂载 controller 路由）
│  │  ├─ config.py                    # 系统配置
│  │  ├─ database.py                  # DB 初始化与会话
│  │  ├─ models.py                    # SQLAlchemy 模型汇总
│  │  ├─ schemas.py                   # Pydantic 请求/响应模型
│  │  ├─ controller/                  # 当前主要 API 控制层（已在 main.py 使用）
│  │  │  ├─ auth_controller.py
│  │  │  ├─ health_data_controller.py
│  │  │  ├─ ai_controller.py
│  │  │  ├─ knowledge_controller.py
│  │  │  └─ admin_controller.py
│  │  ├─ service/                     # 业务服务层
│  │  │  ├─ auth_service.py
│  │  │  ├─ auth_profile_service.py
│  │  │  ├─ blockchain_service.py
│  │  │  ├─ blockchain_encryption_service.py
│  │  │  ├─ ai_service.py
│  │  │  ├─ rag_index_service.py
│  │  │  └─ admin_service.py
│  │  ├─ entity/                      # 分拆实体定义（与 models 并存）
│  │  └─ features/                    # 新分层模块（admin/auth/ai/health_data/knowledge/rag）
│  ├─ scripts/                        # 数据迁移、爬取、重建索引等脚本
│  ├─ tests/                          # P0 自动化测试
│  ├─ requirements.txt
│  └─ seed_health.sql
├─ frontend/
│  ├─ src/
│  │  ├─ main.js
│  │  ├─ App.vue
│  │  ├─ router/index.js              # 路由与登录态守卫
│  │  ├─ api/
│  │  │  ├─ core/http.js              # Axios 基础封装
│  │  │  ├─ modules/                  # 推荐使用的模块化 API
│  │  │  └─ *.js                      # 兼容保留 API
│  │  ├─ views/
│  │  │  ├─ Login.vue / Register.vue
│  │  │  ├─ Dashboard.vue / Home.vue
│  │  │  ├─ HealthData.vue / Profile.vue
│  │  │  ├─ KnowledgeCenter.vue / KnowledgeArticleDetail.vue
│  │  │  ├─ AiAssistant.vue
│  │  │  ├─ AdminDashboard.vue / AdminHome.vue / AdminUsers.vue
│  │  │  ├─ AdminKnowledgeBase.vue / AdminArticles.vue
│  │  │  └─ admin/AdminSettings.vue / admin/AdminLogs.vue / admin/AdminHealthRecords.vue
│  │  └─ utils/auth.js
│  ├─ package.json
│  └─ vite.config.js
├─ contracts/                         # Solidity 合约与编译产物
├─ docs/                              # 设计与测试文档
├─ scripts/                           # 一键启动脚本（开发/生产）
└─ test/                              # JS/性能测试与结果
```

---

## 架构说明（重要）

### 1) 后端当前“生效入口”
`backend/app/main.py` 当前注册的是 `app/controller/*.py` 路由。

### 2) 代码中存在“两套组织方式”并行
- 一套是 `controller + service + models/schemas`（当前运行主路径）
- 一套是 `features/*`（模块化重构路径）

这不是错误，但会提升维护成本。后续建议逐步收敛到一套入口与分层。

### 3) 系统设置已经从“展示”改为“真实生效”
已接入并生效的关键项包括：
- 维护模式：`maintenance_mode`
- 用户注册开关：`allow_user_register`
- 社交登录开关：`allow_social_login`
- 密码最小长度：`password_min_length`
- 会话时长：`session_timeout_minutes`
- AI 总开关：`ai_enabled`
- 知识导入开关：`knowledge_import_enabled`
- 默认健康数据公开策略：`default_health_data_public`

---

## 快速启动（开发）

## 1. 后端

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend\requirements.txt
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

文档地址：
- `http://127.0.0.1:8000/docs`

## 2. 前端

```powershell
cd frontend
npm install
npm run dev
```

访问地址：
- `http://127.0.0.1:3000`

## 3. 依赖服务（可选但推荐）
- MySQL
- Ollama（大模型与 embedding）
- Qdrant（向量库）
- 本地区块链节点（链上存证场景）

---

## 关键业务流（简版）

1. 账号与密钥
- 注册时生成钱包与密钥材料。
- 启动补种子用户时，若缺失密钥会自动补齐（私钥材料/公钥/钱包地址）。

2. 健康数据写入
- 支持手动文本与 PDF/Word。
- 私密数据使用 DEK 包裹加密；公开数据按公开策略处理。
- 上链失败不再静默：接口返回 `onchain_warning`，并写系统告警日志。

3. AI 问答
- 支持用户公开数据与可选私密上下文参与问答。
- 可结合知识库做 RAG 检索增强。

---

## 测试与构建

前端构建：

```powershell
npm --prefix frontend run build
```

后端关键文件语法检查：

```powershell
python -m py_compile backend/app/main.py backend/app/controller/*.py backend/app/service/*.py
```

---

## 后续建议

1. 统一后端分层入口（`controller` 与 `features` 逐步收敛）。
2. 将 `HealthData.vue` 的授权演示（UI Mock）替换为完整后端授权流程（当前页面已有基础接口能力）。
3. 增加“乱码/占位符”静态扫描到 CI，避免 `????` 与异常字符再次进入主分支。
