# 本地大模型接入与 AI 问答改造说明

> 这份文档说明本项目如何连接本地 Ollama 大模型、前后端分别怎么接入 `http://localhost:11434`，以及 AI 问答、RAG、个性化上下文、流式输出、首页 AI 建议等功能目前做了什么。

## 1. 这份文档讲什么

如果把这套 AI 能力拆开来看，核心其实只有三层：

1. **模型层**：本地 Ollama，默认地址 `http://127.0.0.1:11434`
2. **业务层**：后端 FastAPI，把用户问题、健康数据、RAG 检索结果组装成 prompt
3. **展示层**：前端 Vue 页面，负责发起请求、显示流式回答、展示历史记录和私密数据选择弹窗

所以这份文档本质上是在说明：

> 本项目如何把本地部署的大模型真正接入到健康管理系统里，并让 AI 问答从“纯聊天”升级为“结合用户数据 + RAG + 流式交互”的个性化健康助手。

---

## 2. 本地大模型接在哪里

当前核心配置在：

- `backend/app/config.py`

里面已经定义了 Ollama 相关配置：

- `OLLAMA_BASE_URL`：默认 `http://127.0.0.1:11434`
- `OLLAMA_MODEL`：默认 `deepseek-r1:8b`
- `OLLAMA_TIMEOUT_SECONDS`
- `OLLAMA_TEMPERATURE`
- `OLLAMA_TOP_P`
- `OLLAMA_TOP_K`
- `OLLAMA_REPEAT_PENALTY`
- `OLLAMA_NUM_PREDICT`

也就是说，后端不会直接写死模型地址，而是统一从配置中读取。

---

## 3. 后端是怎么连接 Ollama 的

核心文件：

- `backend/app/features/ai/router.py`

其中最关键的函数有：

- `_ollama_request(...)`
- `_call_ollama(...)`
- `_stream_ollama(...)`

### 3.1 非流式调用

后端会向下面这个接口发请求：

- `POST http://127.0.0.1:11434/api/generate`

请求体里会带上：

- `model`
- `system`
- `prompt`
- `stream`
- `options`

其中 `options` 就是模型推理参数，例如：

- `temperature`
- `top_p`
- `top_k`
- `repeat_penalty`
- `num_predict`

### 3.2 流式调用

当用户走流式问答时，后端同样请求：

- `POST /api/generate`

但会把：

- `stream = true`

这样 Ollama 会逐段返回内容，后端再把这些分段转成 SSE 流，继续推给前端。

---

## 4. 前后端如何接入 `http://localhost:11434`

严格来说，**前端并不直接访问 Ollama**，而是：

1. 前端请求自己的后端
2. 后端再请求本地 Ollama

这样做的好处是：

- 前端不用暴露模型地址和推理参数
- 可以在后端统一拼装 prompt
- 可以在后端做鉴权、数据解密、RAG 检索
- 可以统一处理超时、异常和历史记录

### 4.1 前端接后端

前端 AI 接口封装在：

- `frontend/src/api/modules/ai.js`

当前主要接口有：

- `POST /api/ai/chat`
- `POST /api/ai/chat/stream`
- `GET /api/ai/chat/history`
- `GET /api/ai/chat/{chat_id}/messages`
- `GET /api/ai/private-context/options`
- `GET /api/ai/home-advice`

### 4.2 后端接 Ollama

后端 AI 路由在：

- `backend/app/features/ai/router.py`

由它完成：

1. 读取用户问题
2. 读取公开健康数据
3. 读取用户授权的私密数据
4. 检索 RAG 文档
5. 拼装 prompt
6. 调用本地 Ollama
7. 保存聊天记录
8. 把结果返回给前端

---

## 5. AI 问答目前已经做了哪些工作

下面这些能力，已经不是简单“调模型”了，而是做了完整业务接入。

### 5.1 公开健康数据上下文注入

相关文件：

- `backend/app/features/ai/service.py`

已经实现：

- 自动读取用户公开健康记录
- 支持文本记录
- 支持 PDF 健康报告
- 自动提取指标和摘要
- 组装为模型可读的上下文

对应函数主要有：

- `get_public_records(...)`
- `build_public_health_context(...)`
- `build_record_context(...)`
- `extract_pdf_text(...)`

这意味着 AI 问答不是空回答，而是会优先参考用户自己的公开健康数据。

### 5.2 私密数据选择 + 自动解密注入

相关文件：

- `backend/app/features/ai/service.py`
- `backend/app/features/ai/router.py`
- `frontend/src/views/AiAssistant.vue`

已经实现：

- AI 输入框上方有“选择私密数据”按钮
- 可以弹窗列出用户全部可用的非公开档案和非公开健康记录
- 用户勾选后，本次问答会自动读取这些私密数据
- 后端会自动尝试使用用户已托管的私钥进行解密
- 解密结果只作为**当前这一次问答的前置上下文**

对应接口：

- `GET /api/ai/private-context/options`

对应请求字段：

- `selected_private_context_ids`

也就是说，私密数据不是默认全量喂给 AI，而是用户显式选择后才参与回答。

### 5.3 RAG 检索增强

相关文件：

- `backend/app/features/ai/router.py`
- `backend/app/features/knowledge/router.py`
- `backend/app/models.py`

当前 RAG 数据源包括：

- `rag_knowledge_documents`
- `health_articles`

已经实现：

- 根据用户问题抽取检索词
- 在知识库文档和健康文章里做简单相关性匹配
- 按相关度和更新时间选取少量片段
- 把检索结果拼入 prompt

对应核心函数：

- `_query_terms(...)`
- `_score(...)`
- `_rag_context(...)`

另外，管理端已经支持：

- 手动新增 RAG 文档
- 导入 PDF / DOCX 为 RAG 文档
- 导入默认示例 RAG 文档

对应接口例如：

- `POST /api/knowledge/admin/rag-docs`
- `POST /api/knowledge/admin/rag-docs/import`
- `POST /api/knowledge/admin/rag-docs/seed-defaults`

### 5.4 Prompt 工程改造

相关文件：

- `backend/app/features/ai/router.py`

已经做的 prompt 工作包括：

- 区分 `system prompt` 和 `user prompt`
- 将上下文拆成多块：
  - 公开档案
  - 公开健康数据
  - 用户授权的私密数据
  - RAG 检索结果
  - 当前会话历史
- 明确要求：
  - 用中文回答
  - 不编造
  - 不输出思维链
  - 给出可执行建议

首页 AI 建议还单独做了更严格的 JSON prompt，要求模型输出：

- `summary`
- `recommendations`
- `insights`
- `based_on_public_records`

### 5.5 流式输出

相关文件：

- `backend/app/features/ai/router.py`
- `frontend/src/api/modules/ai.js`
- `frontend/src/views/AiAssistant.vue`

已经实现：

- 后端把 Ollama 的流式结果转成 SSE
- 前端逐段接收并拼接
- 支持状态事件和最终完成事件

当前 SSE 事件包括：

- `meta`
- `status`
- `delta`
- `done`
- `error`

这使得用户不需要等整段回答生成完才看到内容。

### 5.6 “停止生成”按钮

前端 AI 页面已经实现：

- 正在生成时显示“停止生成”按钮
- 点击后会中断当前流式请求

这解决了回答过长或生成太慢时无法终止的问题。

### 5.7 流式状态提示

当前 AI 页面在生成过程中会显示状态，例如：

- 正在读取并解密你选择的私密数据
- 正在检索知识库
- 正在整理你的公开健康数据
- 正在生成回答
- 正在保存对话

这比单纯转圈更容易看出卡在什么阶段。

### 5.8 对话历史与会话分组

相关文件：

- `backend/app/models.py`
- `backend/app/database.py`
- `backend/app/features/ai/router.py`

已经做的修复：

- 新增 `chat_messages.session_id`
- 历史记录按 `session_id` 分组
- 每个会话有标题，不再只显示日期
- 点击旧会话时，不再把后续所有消息都混进来

### 5.9 首页 AI 个性化建议

虽然这不属于聊天框本身，但和 AI 问答共用了同一套模型与数据基础。

已经实现：

- 首页建议改为优先调用本地 Ollama
- 使用公开档案、公开健康数据、公开 PDF、RAG 一起生成
- 最新的公开记录权重更高
- 结果缓存到数据库字段 `users.home_ai_advice_cache`
- 用户修改公开资料/公开健康数据后，不立即生成
- 而是在下次进入首页时展示 loading UI，再重新生成

---

## 6. AI 问答一次请求的完整链路

用户在前端发送一句话时，实际流程大致如下：

1. 前端页面 `AiAssistant.vue` 收集：
   - 用户输入
   - 当前会话 `chat_id`
   - 用户勾选的私密数据 ID
2. 前端调用：
   - `/api/ai/chat` 或
   - `/api/ai/chat/stream`
3. 后端保存用户消息
4. 后端读取公开档案和公开健康记录
5. 后端按用户勾选项读取私密档案/私密记录并自动解密
6. 后端执行 RAG 检索
7. 后端拼装 prompt
8. 后端请求 Ollama：`/api/generate`
9. 后端把回答保存到 `chat_messages`
10. 前端显示回答、引用来源、是否用了个性化数据

---

## 7. 与 AI 能力直接相关的数据库对象

### 7.1 聊天记录

- 表：`chat_messages`
- 关键字段：
  - `id`
  - `session_id`
  - `user_id`
  - `message`
  - `is_user`
  - `created_at`

### 7.2 RAG 文档

- 表：`rag_knowledge_documents`

用于存放：

- 管理员录入的知识文档
- 导入的 PDF / DOCX 文本
- 默认示例知识

### 7.3 健康文章

- 表：`health_articles`

这些文章也会作为 AI 问答的 RAG 候选来源。

### 7.4 首页 AI 建议缓存

- 表：`users`
- 字段：`home_ai_advice_cache`

这里存的是已经生成好的首页 AI 建议 JSON，避免用户每次登录都重新跑一次大模型。

---

## 8. 如果要更换模型，改哪里

如果你把本地模型从：

- `deepseek-r1:8b`

换成别的 Ollama 模型，例如：

- `qwen2.5:7b`
- `llama3.1:8b`

通常只需要修改：

- `backend/app/config.py`

或者在环境变量中覆盖：

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=你的模型名
OLLAMA_TIMEOUT_SECONDS=300
OLLAMA_NUM_PREDICT=512
```

前提是：

1. 该模型已经被 Ollama 拉取到本地
2. `ollama list` 能看到该模型
3. 模型名与配置完全一致

---

## 9. 最常见的接入排查点

如果 AI 页面没有回答、回答很慢、或不流式，通常先排查下面几项。

### 9.1 Ollama 是否真的启动

可先检查：

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:11434/api/tags
```

如果返回正常 JSON，说明 Ollama 端口基本可用。

### 9.2 模型名是否一致

比如配置里是：

- `deepseek-r1:8b`

那本地 Ollama 里也必须真有这个模型名。

### 9.3 后端是否通过配置访问了正确地址

检查：

- `backend/app/config.py`

确认不是还在指向别的端口或远程地址。

### 9.4 前端是否请求的是后端流式接口

如果希望看到真正的流式输出，前端应走：

- `/api/ai/chat/stream`

而不是只走一次性返回的：

- `/api/ai/chat`

### 9.5 RAG 数据是否为空

如果知识库没有文档、文章也没相关内容，那么 RAG 能力就很弱，只能依赖模型自身知识和用户数据。

---

## 10. 关键源码文件索引

如果想继续维护这块功能，建议重点看下面这些文件：

### 后端

- `backend/app/config.py`
  - Ollama 模型地址和参数配置
- `backend/app/features/ai/router.py`
  - AI 问答主路由、Ollama 调用、SSE、prompt、首页 AI 建议
- `backend/app/features/ai/service.py`
  - 健康记录/PDF/私密数据/RAG 辅助上下文处理
- `backend/app/features/knowledge/router.py`
  - RAG 文档管理、导入、默认知识导入
- `backend/app/models.py`
  - `ChatMessage`、`RagKnowledgeDocument`、`home_ai_advice_cache`
- `backend/app/database.py`
  - 自动补齐 `session_id`、`home_ai_advice_cache` 字段

### 前端

- `frontend/src/api/modules/ai.js`
  - AI 接口和流式 SSE 解析
- `frontend/src/views/AiAssistant.vue`
  - AI 问答页面、历史记录、私密数据弹窗、流式展示、停止生成
- `frontend/src/views/Home.vue`
  - 首页 AI 个性化建议加载和展示

---

## 11. 一句话总结

`ollama-ai-chat-integration.md` 这份文档讲的其实就是：

> 本项目已经把本地 Ollama 大模型真正接进了业务系统，不只是能聊天，还能结合公开健康数据、用户授权私密数据、PDF 内容、RAG 知识库、会话历史和流式交互，为用户提供更贴近健康场景的个性化 AI 问答与首页建议。

---

## 11. 向量 RAG 实装更新（2026-03-23）

当前项目的 RAG 已从“纯关键词匹配”升级为“**Ollama Embedding + Qdrant 向量检索 + 关键词兜底**”。

### 11.1 当前技术栈

- **LLM**：Ollama / `deepseek-r1:8b`
- **Embedding**：Ollama / `nomic-embed-text`
- **Vector DB**：Qdrant
- **Qdrant Python SDK**：`qdrant-client`
- **业务库**：MySQL

### 11.2 当前向量化范围

当前只对下面这张表做向量化：

- `rag_knowledge_documents`

明确说明：

- `health_articles` **暂时不进入向量库**
- AI 对话里的向量召回来源 **仅来自** `rag_knowledge_documents`

### 11.3 新增的数据结构与模块

新增表：

- `rag_knowledge_chunks`

新增模块：

- `backend/app/features/rag/chunking.py`
- `backend/app/features/rag/embeddings.py`
- `backend/app/features/rag/vector_store.py`
- `backend/app/features/rag/index_service.py`
- `backend/scripts/rebuild_rag_index.py`

其中：

- `chunking.py`：负责知识文档切块
- `embeddings.py`：负责调用 Ollama `/api/embed`
- `vector_store.py`：负责通过 `qdrant-client` 操作 Qdrant
- `index_service.py`：负责建索引、删索引、检索、全量重建

### 11.4 默认配置

目前默认配置为：

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=deepseek-r1:8b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_TIMEOUT_SECONDS=300
OLLAMA_NUM_PREDICT=1024
AI_RAG_LIMIT=3
RAG_VECTOR_BASE_URL=http://127.0.0.1:6333
RAG_VECTOR_COLLECTION=health_rag_documents
RAG_VECTOR_TOP_K=6
RAG_CHUNK_SIZE=500
RAG_CHUNK_OVERLAP=80
```

说明：

- `AI_RAG_LIMIT=3`：最终最多拼接 3 条 RAG 结果进 prompt
- `RAG_VECTOR_TOP_K=6`：先从向量库召回更多候选，再做简单重排
- `OLLAMA_NUM_PREDICT=1024`：用于兼容当前 `deepseek-r1:8b` 在本地生成回答时的输出长度需求

### 11.5 索引同步时机

以下操作会自动同步向量索引：

- `POST /api/knowledge/admin/rag-docs`
- `POST /api/knowledge/admin/rag-docs/import`
- `POST /api/knowledge/admin/rag-docs/seed-defaults`
- `PUT /api/knowledge/admin/rag-docs/{doc_id}`
- `DELETE /api/knowledge/admin/rag-docs/{doc_id}`

### 11.6 Docker 启动 Qdrant

本地验证使用的命令：

```bash
docker run -d --name health-qdrant -p 6333:6333 ghcr.io/qdrant/qdrant/qdrant:v1.16.3
```

### 11.7 全量重建索引

```bash
.venv\Scripts\python.exe backend\scripts\rebuild_rag_index.py
```

成功示例：

```text
RAG index rebuild completed.
documents_total=5
documents_indexed=5
chunks_indexed=5
```

### 11.8 已完成真实接口联调

已完成一次真实接口测试：

1. 启动后端
2. 管理员登录：`POST /api/auth/admin/login`
3. AI 聊天：`POST /api/ai/chat`

测试问题：

> 高血压怎么居家监测？请结合知识库，简短回答并给3条建议

测试结果：

- 接口返回成功
- 返回内容包含健康建议
- `references` 已带回知识库引用
- 当前问答链路已确认接通 Ollama + Qdrant + MySQL
