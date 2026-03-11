# 项目学习指南

> 面向计算机专业学生的项目理解文档。
> 目标：帮助你快速理解这个健康管理系统“用了什么技术、怎么跑起来、模块如何协作、每个重要文件在做什么”。

## 1. 项目一句话概括

这是一个 **前后端分离的健康管理系统**，采用：

- 前端：`Vue 3 + Vite + Element Plus + Vue Router + Axios`
- 后端：`FastAPI + SQLAlchemy + Pydantic + MySQL`
- 扩展能力：`JWT 鉴权`、`健康数据分析`、`健康知识中心`、`AI 问答`、`区块链/Web3`、`管理后台`

系统分为两个主要入口：

- 普通用户端：查看首页、健康数据、健康知识、AI 助手、个人中心
- 管理员端：用户管理、文章管理、知识库管理、系统设置、系统日志

---

## 2. 你应该先掌握哪些关键技术

如果你想真正看懂这个项目，建议重点理解下面这些知识点：

### 2.1 前端相关

1. **Vue 3 组件化开发**
   - 每个页面通常是一个 `.vue` 文件
   - 一个 `.vue` 文件通常包含三部分：
     - `template`：页面结构
     - `script setup`：页面逻辑
     - `style`：样式

2. **Vue Router 路由系统**
   - 决定 URL 对应哪个页面组件
   - 本项目中：
     - `/login` -> 登录页
     - `/dashboard/...` -> 用户端页面
     - `/admin/...` -> 管理端页面

3. **Axios / 统一 HTTP 封装**
   - 前端通过 HTTP 请求访问后端 API
   - 本项目做了统一封装，自动带 token、统一处理 401 未登录

4. **Element Plus 组件库**
   - 表格、表单、弹窗、分页、按钮、消息提示，很多都是它提供的

5. **状态来源主要是 localStorage**
   - 本项目没有大量使用 Pinia 存业务状态
   - 登录 token、用户名、角色主要存在 `localStorage`

### 2.2 后端相关

1. **FastAPI**
   - Python Web 框架
   - 用装饰器声明接口，比如：
     - `@router.get(...)`
     - `@router.post(...)`

2. **SQLAlchemy ORM**
   - 把数据库表映射成 Python 类
   - 例如 `User`、`HealthData`、`HealthArticle`
   - 你操作的是对象，底层才转成 SQL

3. **Pydantic / Schema**
   - 定义请求参数和响应结构
   - 相当于“接口契约”
   - 例如：前端发什么字段、后端返回什么字段，都可以在 `schemas.py` 里看出

4. **JWT 鉴权**
   - 用户登录后，后端返回 token
   - 前端把 token 放进请求头
   - 后端通过依赖注入判断当前用户是谁、是不是管理员

5. **依赖注入（Depends）**
   - FastAPI 常见写法
   - 例如数据库会话、当前登录用户，都是通过 `Depends(...)` 自动注入

### 2.3 数据与安全相关

1. **用户角色控制（RBAC 的简化版本）**
   - `user`：普通用户
   - `admin`：管理员
   - 前端路由和后端接口都会做权限判断

2. **阅读历史与收藏关系表**
   - 阅读历史不是简单提示，而是单独建表记录
   - 收藏也有单独关系表
   - 这是典型的“用户行为数据建模”思路

3. **知识库 / RAG 文档思路**
   - 管理员可以维护知识库文档
   - AI 回答时会检索这些文档，增强回答内容
   - 这是一个典型的“检索增强生成（RAG）”项目雏形

4. **文件导入**
   - 当前知识库支持从 `PDF` 和 `DOCX` 提取文本并导入数据库
   - 本质上是：文件解析 -> 文本清洗 -> 落库

### 2.4 区块链相关

1. **Web3.py / Solidity**
   - 项目不是纯 Web 系统，还尝试引入区块链能力
   - 用智能合约保存或验证健康数据访问相关信息

2. **私钥派生与加密**
   - 项目中有私钥、地址、哈希、对称加密等逻辑
   - 这是“区块链身份 + 本地数据隐私”结合的典型设计

---

## 3. 项目总体架构

你可以把整个系统理解成下面这条链路：

1. 用户打开前端页面（Vue）
2. 页面组件通过 API 模块发送 HTTP 请求（Axios）
3. FastAPI 接收请求
4. 路由层调用数据库模型和业务逻辑
5. SQLAlchemy 访问 MySQL
6. 返回结构化 JSON 给前端
7. 前端渲染成表格、卡片、详情页等界面

如果涉及 AI 或知识库，则流程会变成：

1. 前端提交问题
2. 后端 AI 模块读取用户公开健康数据
3. 再从知识库中检索相关文档
4. 组合上下文生成回答
5. 返回给前端展示

如果涉及区块链，则还有额外一步：

1. 后端调用 Web3 服务
2. 把某些数据哈希或链上记录写入智能合约

---

## 4. 前后端是怎么协作的

### 4.1 登录流程

统一登录页在前端输入账号密码后：

1. 前端调用认证接口
2. 后端校验用户
3. 后端返回 token 和用户角色
4. 前端把 token、用户名、角色存入 `localStorage`
5. 根据角色跳转：
   - 普通用户 -> `/dashboard`
   - 管理员 -> `/admin`

### 4.2 路由守卫流程

前端路由守卫会做这些事：

- 没 token：跳回 `/login`
- 访问管理员页面但不是管理员：跳回 `/login`
- 管理员如果去普通用户入口，会被重定向回 `/admin`

### 4.3 知识中心流程

1. 前端调用文章列表接口
2. 后端查询 `health_articles`
3. 同时统计阅读量、收藏量、是否已收藏
4. 返回给前端
5. 用户点开详情时，后端更新阅读记录
6. 用户点击收藏 / 取消收藏时，更新收藏关系表

### 4.4 管理端知识库导入流程

1. 管理员在管理端选择 PDF / DOCX 文件
2. 前端把文件作为 `multipart/form-data` 上传
3. 后端解析文件文本
4. 生成知识库文档记录
5. 存入 `rag_knowledge_documents`
6. AI 模块后续可以拿这些文档做知识增强

---

## 5. 数据库层面你要重点理解什么

从 `backend/app/models.py` 可以看出，这个项目的数据库设计至少包含以下几类核心实体：

- `User`：用户表
- `UserProfile`：用户资料表
- `HealthData`：健康数据表
- `HealthArticle`：健康文章表
- `RagKnowledgeDocument`：知识库文档表
- `ArticleFavorite`：文章收藏关系表
- `ArticleReadHistory`：文章阅读历史表
- `ChatHistory` / `ChatMessage`：AI 聊天记录相关表
- `AdminSystemSetting`：系统设置表
- `AdminSystemLog`：系统日志表

### 关键建模思想

1. **主实体 + 行为关系表**
   - 文章是主实体
   - 收藏、阅读历史是关系表
   - 这是非常常见的数据库设计方式

2. **一对多 / 多对一关系**
   - 一个用户可以有多条健康数据
   - 一个文章可以被多个用户收藏

3. **冗余字段与统计字段**
   - 像 `view_count` 这种字段是统计字段
   - 但项目里又通过阅读历史表做更真实的统计
   - 这体现了“缓存字段”和“真实行为表”的区别

---

## 6. 这个项目最值得你学习的知识点

### 6.1 分层思想

这个项目虽然不算特别严格的企业级架构，但已经体现出基本分层：

- 前端表现层：页面、组件、路由
- 前端接口层：API 封装
- 后端路由层：定义接口
- 后端模型层：数据库模型
- 后端 Schema 层：请求/响应结构
- 后端服务层：部分模块有独立 service

### 6.2 路由与权限的双重控制

- 前端做页面级控制
- 后端做接口级控制

这点很重要，因为：

- 只做前端控制，不安全
- 只做后端控制，用户体验差
- 两边都做，才是完整方案

### 6.3 数据模型驱动页面

很多页面其实都可以抽象成：

- 列表页：查列表
- 详情页：查一条
- 表单页：新增 / 编辑
- 行为接口：收藏、删除、切换状态

这就是“前后端管理系统”的典型模式。

### 6.4 文件上传与解析

你可以通过知识库导入功能学会：

- 前端如何上传文件
- 后端如何接收 `UploadFile`
- 如何按后缀选择解析器
- 如何把解析结果转成数据库记录

### 6.5 AI 模块的工程化思路

这个项目的 AI 不是单纯调一个聊天框，而是尝试结合：

- 用户公开健康数据
- 知识库文档
- 历史聊天记录

这比“纯聊天 DEMO”更接近真实系统。

---

## 7. 核心运行入口

### 7.1 前端入口

- `frontend/src/main.js`
  - 创建 Vue 应用
  - 注册 Pinia、Router、Element Plus、图标

- `frontend/src/App.vue`
  - 最外层壳组件
  - 主要作用是渲染 `<router-view />`

- `frontend/src/router/index.js`
  - 定义所有页面路由
  - 定义登录拦截、管理员权限控制、登录后跳转逻辑

### 7.2 后端入口

- `backend/app/main.py`
  - 创建 FastAPI 应用
  - 挂载各功能模块路由
  - 初始化数据库和默认管理员
  - 配置 CORS 等中间件

- `backend/app/database.py`
  - 创建 SQLAlchemy 引擎、会话工厂
  - 提供 `get_db()` 给路由使用

- `backend/app/config.py`
  - 全局配置项
  - 数据库、JWT、管理员默认账户、Web3 配置等

---

## 8. 文件职责索引（核心源码）

> 说明：这里重点解释“源码文件”和“关键脚本文件”。
> `node_modules`、`__pycache__`、日志文件、编译产物、链上编译缓存等自动生成文件不逐个展开。

### 8.1 根目录

- `README.md`
  - 项目总体说明文档
  - 当前存在编码问题，可作为旧说明参考

- `start.py`
  - 项目启动辅助脚本
  - 用于串联启动后端、前端，或做环境检查

- `test_register.py`
  - 一个独立的注册测试脚本
  - 用来验证注册接口是否正常

- `.gitignore`
  - Git 忽略规则

### 8.2 backend 根目录

- `backend/requirements.txt`
  - Python 依赖列表
  - 包括 FastAPI、SQLAlchemy、Web3、文件解析库等

- `backend/seed_health.sql`
  - 数据库初始化 SQL
  - 适合快速建立基础表和种子数据

- `backend/seed_health_articles.sql`
  - 健康文章相关的初始数据脚本

- `backend/import_seed_articles.py`
  - 导入文章种子数据的辅助脚本

- `backend/simple_main.py`
  - 简化版后端入口，适合调试或实验

- `backend/test_basic.py`
  - 后端基础功能测试脚本

- `backend/backend.log`
  - 后端运行日志

- `backend/backend.err.log`
  - 后端错误日志

### 8.3 backend/app 基础层

- `backend/app/__init__.py`
  - Python 包初始化文件

- `backend/app/main.py`
  - FastAPI 主入口

- `backend/app/config.py`
  - 读取和集中管理系统配置

- `backend/app/database.py`
  - 数据库连接、会话、依赖注入

- `backend/app/models.py`
  - 数据库 ORM 模型定义
  - 项目最重要的底层文件之一

- `backend/app/schemas.py`
  - Pydantic 数据结构定义
  - 定义所有请求体和响应体

### 8.4 backend/app/features/auth

- `backend/app/features/auth/router.py`
  - 认证与用户相关接口
  - 包括注册、登录、社交登录、获取当前用户、管理员用户管理等

- `backend/app/features/auth/service.py`
  - 认证业务逻辑
  - 例如密码处理、用户创建、管理员初始化等

- `backend/app/features/auth/profile_service.py`
  - 用户资料相关业务逻辑
  - 处理资料公开/私密等逻辑

- `backend/app/features/auth/dependencies.py`
  - 登录态解析、当前用户获取等依赖函数

- `backend/app/features/auth/__init__.py`
  - 包初始化

### 8.5 backend/app/features/health_data

- `backend/app/features/health_data/router.py`
  - 健康数据相关接口
  - 包括新增、查询、更新、删除、统计摘要、分析等

- `backend/app/features/health_data/__init__.py`
  - 包初始化

### 8.6 backend/app/features/knowledge

- `backend/app/features/knowledge/router.py`
  - 健康知识与知识库核心模块
  - 包含：文章列表、详情、收藏、阅读历史、推荐
  - 也包含管理端文章管理、知识库管理、PDF/DOCX 导入等

- `backend/app/features/knowledge/__init__.py`
  - 包初始化

### 8.7 backend/app/features/ai

- `backend/app/features/ai/router.py`
  - AI 助手模块
  - 包括对话、历史消息、健康建议、AI 分析等

- `backend/app/features/ai/__init__.py`
  - 包初始化

### 8.8 backend/app/features/blockchain

- `backend/app/features/blockchain/service.py`
  - 区块链交互服务
  - 负责与合约、Web3 连接打交道

- `backend/app/features/blockchain/encryption.py`
  - 私钥相关的加解密逻辑
  - 包括地址推导、哈希、文本/二进制加解密

- `backend/app/features/blockchain/__init__.py`
  - 包初始化

### 8.9 backend/app/features/admin

- `backend/app/features/admin/router.py`
  - 管理端系统设置和系统日志接口

- `backend/app/features/admin/service.py`
  - 管理端配置相关业务逻辑

- `backend/app/features/admin/__init__.py`
  - 包初始化

### 8.10 backend 其他目录

- `backend/app/dependencies/__init__.py`
  - 旧依赖目录占位

- `backend/app/routers/__init__.py`
  - 旧路由目录占位
  - 当前项目主要已经迁移到 `features/*/router.py`

- `backend/app/services/__init__.py`
  - 旧 service 目录占位

### 8.11 frontend 根目录

- `frontend/package.json`
  - 前端依赖、脚本命令定义

- `frontend/package-lock.json`
  - npm 锁定依赖版本

- `frontend/vite.config.js`
  - Vite 打包与开发服务器配置

- `frontend/index.html`
  - 前端 HTML 模板入口

- `frontend/frontend.log`
  - 前端开发服务日志

- `frontend/frontend.err.log`
  - 前端错误日志

### 8.12 frontend/src 基础层

- `frontend/src/main.js`
  - Vue 应用入口

- `frontend/src/App.vue`
  - 最外层根组件

- `frontend/src/router/index.js`
  - 前端路由表和权限守卫

- `frontend/src/utils/auth.js`
  - 前端鉴权工具函数
  - 负责清理 token、跳转登录页等

### 8.13 frontend/src/api 顶层导出文件

这些文件主要是“统一导出入口”，便于页面通过一个简洁路径引入：

- `frontend/src/api/auth.js`
- `frontend/src/api/health.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/ai.js`
- `frontend/src/api/adminSystem.js`

### 8.14 frontend/src/api/core

- `frontend/src/api/core/http.js`
  - Axios 二次封装
  - 自动附加 token
  - 自动处理 401 未授权
  - 统一 baseURL

### 8.15 frontend/src/api/modules

- `frontend/src/api/modules/auth.js`
  - 认证接口封装

- `frontend/src/api/modules/health.js`
  - 健康数据接口封装

- `frontend/src/api/modules/knowledge.js`
  - 文章、收藏、阅读记录、知识库管理、文件导入接口封装

- `frontend/src/api/modules/ai.js`
  - AI 聊天与分析接口封装

- `frontend/src/api/modules/adminSystem.js`
  - 管理端系统设置与日志接口封装

### 8.16 frontend/src/views 用户端页面

- `frontend/src/views/Login.vue`
  - 统一登录页
  - 支持根据角色跳转用户端或管理端

- `frontend/src/views/Register.vue`
  - 注册页面

- `frontend/src/views/Dashboard.vue`
  - 用户端主框架页
  - 常见作用是布局、侧边栏、顶部栏、子路由出口

- `frontend/src/views/Home.vue`
  - 用户首页

- `frontend/src/views/HealthData.vue`
  - 健康数据管理页

- `frontend/src/views/KnowledgeCenter.vue`
  - 健康知识中心文章列表页

- `frontend/src/views/KnowledgeArticleDetail.vue`
  - 文章详情页
  - 负责阅读、收藏等交互

- `frontend/src/views/AiAssistant.vue`
  - AI 助手主页面

- `frontend/src/views/Profile.vue`
  - 用户个人中心页面

### 8.17 frontend/src/views 管理端页面

- `frontend/src/views/AdminDashboard.vue`
  - 管理端总布局页
  - 管理菜单、头部、退出登录、子路由承载

- `frontend/src/views/AdminHome.vue`
  - 管理端首页 / 控制台

- `frontend/src/views/AdminUsers.vue`
  - 用户管理页面

- `frontend/src/views/AdminArticles.vue`
  - 健康文章管理页面

- `frontend/src/views/AdminKnowledgeBase.vue`
  - 知识库管理页面
  - 支持新增文档、编辑、删除、导入 PDF / DOCX、导入示例数据

- `frontend/src/views/admin/AdminSettings.vue`
  - 系统设置页面

- `frontend/src/views/admin/AdminLogs.vue`
  - 系统日志页面

### 8.18 frontend/src/views 中的可能遗留文件

- `frontend/src/views/AuthPortal.vue`
  - 看文件名像是旧版登录/认证门户
  - 当前主路由未使用

- `frontend/src/views/AIChat.vue`
  - 看文件名像旧版 AI 页面
  - 当前主路由实际使用的是 `AiAssistant.vue`

### 8.19 contracts 智能合约目录

- `contracts/HealthDataAccess.sol`
  - 健康数据访问控制相关合约

- `contracts/UserAuth.sol`
  - 用户认证 / 身份相关合约

- `contracts/Identity.sol`
  - 身份相关实验性合约

- `contracts/SimpleUserFlow.sol`
  - 一个简化的用户流程合约示例

- `contracts/artifacts/*`
  - 合约编译产物（ABI、metadata、build-info）
  - 后端或测试可能会读取 ABI 与合约交互

### 8.20 docs 文档目录

- `docs/README.md`
  - docs 目录说明

- `docs/architecture.md`
  - 架构说明文档（当前较简略）

- `docs/project-guide.md`
  - 也就是你现在阅读的这份学习文档

### 8.21 test 测试与链上实验目录

- `test/package.json`
  - 测试目录自己的 Node 依赖声明

- `test/package-lock.json`
  - 锁定测试依赖版本

- `test/test_ganache.js`
  - Ganache 相关测试脚本

- `test/test_simple_user_flow.js`
  - 简化链上用户流程测试脚本

- `test/杂.js`
  - 实验/调试性质脚本

- `test/node_modules/*`
  - 测试环境依赖，不属于项目核心源码

---

## 9. 建议你按什么顺序读源码

如果你现在是学生，建议按下面顺序学习，不容易乱：

### 第一轮：先看“整体入口”

1. `frontend/src/main.js`
2. `frontend/src/router/index.js`
3. `backend/app/main.py`
4. `backend/app/models.py`
5. `backend/app/schemas.py`

目的：先建立“页面 -> 接口 -> 数据库”的整体地图。

### 第二轮：看认证链路

1. `frontend/src/views/Login.vue`
2. `frontend/src/api/modules/auth.js`
3. `backend/app/features/auth/router.py`
4. `backend/app/features/auth/service.py`
5. `backend/app/features/auth/dependencies.py`

目的：搞清楚登录、token、角色跳转、权限控制。

### 第三轮：看一个最完整的业务模块

建议你选 **知识中心模块**：

1. `frontend/src/views/KnowledgeCenter.vue`
2. `frontend/src/views/KnowledgeArticleDetail.vue`
3. `frontend/src/api/modules/knowledge.js`
4. `backend/app/features/knowledge/router.py`
5. `backend/app/models.py` 中的文章、收藏、阅读历史相关模型

目的：这条链路最适合学习“前后端协作 + 数据建模 + 用户行为记录”。

### 第四轮：看管理端

1. `frontend/src/views/AdminDashboard.vue`
2. `frontend/src/views/AdminArticles.vue`
3. `frontend/src/views/AdminKnowledgeBase.vue`
4. `backend/app/features/admin/router.py`
5. `backend/app/features/knowledge/router.py` 的 admin 部分

目的：理解管理后台本质上就是 CRUD 系统。

### 第五轮：看扩展能力

1. `backend/app/features/ai/router.py`
2. `backend/app/features/blockchain/service.py`
3. `backend/app/features/blockchain/encryption.py`
4. `contracts/*.sol`

目的：理解 AI 和区块链是怎么作为“增强模块”接入业务系统的。

---

## 10. 这个项目适合你写进简历的点

如果你做课程设计、毕业设计或求职项目，这个项目可以提炼出这些亮点：

- 基于 `Vue 3 + FastAPI` 的前后端分离系统
- 实现了普通用户端与管理员端的角色隔离
- 使用 `JWT` 完成身份认证与权限控制
- 使用 `SQLAlchemy ORM` 完成数据库建模与关系管理
- 实现文章收藏、阅读记录、知识库导入等完整业务闭环
- 结合 `AI + 知识库` 进行健康问答增强
- 尝试集成 `Web3/区块链` 做身份和隐私相关扩展

---

## 11. 你接下来最值得动手研究的 6 个问题

1. 登录成功后，前端究竟把哪些字段存进了 `localStorage`？
2. 后端是怎么判断“当前请求是不是管理员”的？
3. 阅读量为什么不能只靠文章表里的一个数字？
4. 收藏关系为什么需要单独建表？
5. PDF / DOCX 导入为什么最终要转成纯文本再入库？
6. AI 回答为什么要结合知识库，而不是只调用模型？

如果你把这 6 个问题都想明白，这个项目你就不只是“会跑”，而是真的“会讲”。

---

## 12. 一句话总结

这个项目本质上是一个：

**以健康数据和健康知识为核心，集成用户权限、管理后台、AI 辅助和区块链扩展能力的全栈工程项目。**

它最适合你学习的不是某一个单独技术，而是：

**一个真实项目如何把前端、后端、数据库、权限、文件导入、AI 和链上扩展整合在一起。**
