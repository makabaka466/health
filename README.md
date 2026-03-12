# 健康管理系统

基于 **Vue 3 + FastAPI + MySQL + Web3** 的健康管理平台，支持健康数据管理、AI 辅助分析、健康文章管理，以及基于私钥的隐私访问控制（公开/私密）。

---

## 核心能力

- 🔐 用户注册时自动生成钱包地址与一次性私钥（仅返回一次）
- 🔑 支持微信/支付宝第三方登录（首次登录补全资料，后续可一键登录）
- 🧾 个人资料支持公开/私密模式
- 📊 健康数据支持文本/PDF，支持公开/私密存储
- � AI 助手支持对话与健康建议
- 📚 健康文章支持后台管理、收藏与阅读历史
- ⛓️ 健康数据可选上链（Ganache / EVM）
- �️ 管理后台支持系统设置与系统日志

---

## 技术栈

### 后端
- FastAPI
- SQLAlchemy
- MySQL
- Pydantic
- JWT
- Web3.py
- cryptography (Fernet)

### 前端
- Vue 3
- Element Plus
- Vue Router
- Axios
- Web3.js

### 链上
- Solidity 合约（`HealthDataAccess.sol` / `UserAuth.sol`）
- Ganache（默认 `http://127.0.0.1:7545`）

---

## 按功能域分类后的项目结构

```text
健康管理系统/
├─ backend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ config.py
│  │  ├─ database.py
│  │  ├─ models.py
│  │  ├─ schemas.py
│  │  ├─ features/
│  │  │  ├─ auth/            # 登录注册、鉴权依赖、个人资料
│  │  │  ├─ health_data/     # 健康数据 CRUD、公开/私密、分析
│  │  │  ├─ knowledge/       # 健康文章与阅读行为
│  │  │  ├─ ai/              # AI 对话与建议
│  │  │  ├─ blockchain/      # 区块链交互与加解密
│  │  │  └─ admin/           # 系统设置与系统日志
│  │  ├─ routers/            # 预留（当前已迁移到 features）
│  │  └─ services/           # 预留（当前已迁移到 features）
│  ├─ seed_health.sql        # 一键初始化数据库结构与种子数据
│  └─ requirements.txt
├─ frontend/
│  ├─ src/
│  │  ├─ views/
│  │  │  └─ admin/           # 管理端页面（系统设置/日志等）
│  │  ├─ api/
│  │  │  ├─ core/http.js     # 统一 HTTP 客户端
│  │  │  └─ modules/         # 按功能 API 模块拆分
│  │  └─ router/
└─ contracts/
```

---

## 快速启动

## 1) 初始化数据库（推荐）

```bash
mysql -u root -p < backend/seed_health.sql
```

> `seed_health.sql` 为重建型脚本，执行会清空并重建表结构。

## 2) 启动后端

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 3) 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认访问：`http://localhost:3000`

---

## 环境变量（后端）

可通过环境变量覆盖 `backend/app/config.py` 默认值：

- `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME`
- `SECRET_KEY`
- `ADMIN_USERNAME` / `ADMIN_EMAIL` / `ADMIN_PASSWORD` / `ADMIN_REGISTER_KEY`
- `WEB3_PROVIDER_URI`（默认 `http://127.0.0.1:7545`）
- `HEALTH_DATA_CONTRACT_ADDRESS`
- `HEALTH_DATA_CONTRACT_ABI_JSON`

---

## 区块链与隐私说明

1. 用户注册成功后返回一次性 `generated_private_key`。  
2. 数据库只保存 `private_key_hash`，不保存明文私钥。  
3. 私密数据（个人资料、私密健康记录）需提供私钥才可解密查看。  
4. 公开数据可直接访问（公开接口或公开资料接口）。  
5. 若配置了合约地址和 ABI，健康数据会触发可选上链写入（保存交易哈希）。


[用户填写健康数据/上传PDF]
            |
            v
[前端调用 /api/health/records]
            |
            v
[后端校验 JWT，识别当前用户]
            |
            v
[判断 is_public 是否为公开]
      /                    \
     /是                     \否
    v                        v
[明文保存]             [校验 private_key]
    |                        |
    |                        v
    |                 [用私钥派生 Fernet 密钥]
    |                        |
    |                        v
    |                 [文本/PDF 加密]
    |                        |
    \________________________/
             |
             v
      [写入 MySQL 数据库]
             |
             v
[如果本次显式传了 private_key 且链服务已启用]
             |
             v
[计算原始内容 SHA-256]
             |
             v
[调用智能合约 storeHealthData]
             |
             v
[返回 tx_hash，写入数据库 onchain_tx_hash]
             |
             v
         [上传完成]


================ 查看阶段 ================

[用户查看健康数据]
            |
            v
[前端调用 /api/health/records 或 /records/{id}]
            |
            v
[后端读取数据库记录]
            |
            v
[判断该记录是否私密且是否有密文字段]
      /                    \
     /否                     \是
    v                        v
[直接返回明文]         [尝试解密]
                              |
              ┌───────────────┴───────────────┐
              |                               |
              v                               v
      [解密成功，返回真实内容]      [解密失败，返回 requires_private_key=true]
                                              |
                                              v
                                 [前端提示用户输入原始私钥]
                                              |
                                              v
                                   [重新请求并带 private_key]
                                              |
                                              v
                                        [解密后查看]

---

## 默认种子账号

由后端启动初始化自动确保存在：

- 管理员：`admin / admin123`
- 普通用户：`xiaoming / 123456`
- 普通用户：`xiaohong / 123456`

管理员注册密钥默认：`123`

---

## API 文档

- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 第三方登录相关接口

- `POST /api/auth/social/login-init`
  - 入参：`provider`（wechat/alipay）、`auth_code`（第三方授权码，当前项目可使用模拟码）
  - 出参：
    - 已绑定账号：直接返回登录 token
    - 未绑定账号：返回 `social_ticket`，用于下一步补全资料

- `POST /api/auth/social/complete`
  - 入参：`social_ticket` + `username` + `email` + `password`
  - 出参：登录 token

> 说明：当前仓库默认接入为“可跑通的模拟授权码模式”，便于本地联调；生产环境请替换为微信/支付宝官方 OAuth 授权码。

---

## 说明

该项目面向教学与原型验证。生产使用前请补充：

- 完整迁移体系（Alembic）
- 密钥托管与轮换机制
- 更细粒度审计与告警
- 安全压测与备份策略



