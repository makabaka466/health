# 健康管理系统

基于 **Vue 3 + FastAPI + MySQL + Ollama + Qdrant** 的健康管理平台，支持用户健康档案管理、健康知识库、AI 问答、私密数据解密、以及基于本地大模型的向量检索增强问答（RAG）。

## 当前已实现的核心能力

- 用户注册、登录、鉴权
- 健康数据管理：文本 / PDF 上传、公开 / 私密存储
- 健康知识文章管理与阅读历史、收藏
- AI 助手问答：支持非流式与流式输出
- 用户公开健康数据注入 AI 上下文
- 用户主动选择私密数据参与本次问答
- 本地 Ollama 模型推理
- Qdrant 向量检索增强问答（RAG）
- 管理端知识库维护：手动新增、编辑、删除、批量导入 PDF / DOCX

---

## 技术栈

### 后端
- FastAPI
- SQLAlchemy
- MySQL
- PyMySQL
- Pydantic
- python-jose / JWT
- Web3.py
- pypdf
- python-docx
- qdrant-client

### 前端
- Vue 3
- Vite
- Element Plus
- Vue Router
- Axios

### AI / RAG
- Ollama
  - 生成模型：`deepseek-r1:8b`
  - 向量模型：`nomic-embed-text`
- Qdrant
- 本地分块与向量化索引

---

## 项目结构

```text
健康管理系统/
├─ backend/
│  ├─ app/
│  │  ├─ config.py
│  │  ├─ database.py
│  │  ├─ main.py
│  │  ├─ models.py
│  │  ├─ schemas.py
│  │  └─ features/
│  │     ├─ admin/
│  │     ├─ ai/
│  │     ├─ auth/
│  │     ├─ blockchain/
│  │     ├─ health_data/
│  │     ├─ knowledge/
│  │     └─ rag/
│  ├─ scripts/
│  │  └─ rebuild_rag_index.py
│  ├─ requirements.txt
│  └─ seed_health.sql
├─ frontend/
├─ docs/
├─ contracts/
└─ README.md
```

---

## 本地开发启动

## 1. 准备 MySQL

默认配置见 `backend/app/config.py`：

- `DB_HOST=127.0.0.1`
- `DB_PORT=3306`
- `DB_USER=root`
- `DB_PASSWORD=123456`
- `DB_NAME=health`

如需初始化数据库，可执行：

```powershell
mysql -u root -p < backend/seed_health.sql
```

> `seed_health.sql` 会重建部分表结构，执行前请确认是否需要备份数据。

## 2. 准备 Python 虚拟环境并安装后端依赖

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend\requirements.txt
```

## 3. 启动 Qdrant

```powershell
docker run -d --name health-qdrant -p 6333:6333 ghcr.io/qdrant/qdrant/qdrant:v1.16.3
```

如容器已经存在，可直接启动：

```powershell
docker start health-qdrant
```

Qdrant 默认地址：

- `http://127.0.0.1:6333`

## 4. 准备 Ollama 模型

确认本地已经拉取：

```powershell
ollama list
```

建议至少包含：

- `deepseek-r1:8b`
- `nomic-embed-text`

若未安装，可执行：

```powershell
ollama run deepseek-r1:8b
ollama run nomic-embed-text
```

## 5. 启动后端

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

接口文档：

- Swagger：`http://127.0.0.1:8000/docs`
- ReDoc：`http://127.0.0.1:8000/redoc`

## 6. 启动前端

```powershell
cd frontend
npm install
npm run dev
```

默认访问地址：

- `http://127.0.0.1:3000`

---

## AI 与向量 RAG 说明

当前项目中的 AI 问答已经接入本地 Ollama，并升级为向量检索版 RAG。

### 当前实际方案

- **仅 `rag_knowledge_documents` 做向量化**
- **`health_articles` 暂时不进入向量库**
- 向量由本地 Ollama `nomic-embed-text` 生成
- 向量库存储在 Qdrant 集合：`health_rag_documents`
- 文档原文存储在 MySQL：`rag_knowledge_documents`
- 文档分块元数据存储在 MySQL：`rag_knowledge_chunks`

### 索引构建流程

1. 管理端录入或导入知识文档
2. 后端按配置进行文本分块
3. 调用 Ollama embedding 接口生成向量
4. 写入 Qdrant
5. 同时把 chunk 元数据写入 `rag_knowledge_chunks`
6. AI 问答时先检索向量，再把命中内容拼入 prompt

### 重建 RAG 索引

当你批量导入、修改大量知识文档，或者想全量重建向量索引时，可以执行：

```powershell
.\.venv\Scripts\python.exe backend\scripts\rebuild_rag_index.py
```

---

## 关键配置项

以下配置位于 `backend/app/config.py`，也可以通过环境变量覆盖：

### 数据库
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `DATABASE_URL`

### 管理员账号
- `ADMIN_USERNAME`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`
- `ADMIN_REGISTER_KEY`

### Ollama
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `OLLAMA_TIMEOUT_SECONDS`
- `OLLAMA_TEMPERATURE`
- `OLLAMA_TOP_P`
- `OLLAMA_TOP_K`
- `OLLAMA_REPEAT_PENALTY`
- `OLLAMA_NUM_PREDICT`
- `OLLAMA_EMBEDDING_MODEL`
- `OLLAMA_EMBEDDING_TIMEOUT_SECONDS`

### RAG
- `AI_RAG_LIMIT`（当前默认 `3`）
- `AI_CHAT_HISTORY_LIMIT`
- `RAG_VECTOR_ENABLED`
- `RAG_VECTOR_COLLECTION`
- `RAG_VECTOR_BASE_URL`
- `RAG_VECTOR_TIMEOUT_SECONDS`
- `RAG_VECTOR_TOP_K`
- `RAG_VECTOR_SCORE_THRESHOLD`
- `RAG_CHUNK_SIZE`
- `RAG_CHUNK_OVERLAP`

### 区块链
- `WEB3_PROVIDER_URI`
- `HEALTH_DATA_CONTRACT_ADDRESS`
- `HEALTH_DATA_CONTRACT_ABI_JSON`

---

## RAG 知识库如何录入数据

当前已经提供完整的后台录入能力，推荐优先使用管理端页面或管理接口，而不是直接手改数据库。

### 方式一：管理端手动新增

适合：整理好的短篇知识、制度说明、健康建议、FAQ。

可通过管理端知识库页面新增文档，填写：

- 标题
- 分类
- 来源
- 标签
- 正文内容
- 是否启用

对应接口：

- `GET /api/knowledge/admin/rag-docs`
- `POST /api/knowledge/admin/rag-docs`
- `PUT /api/knowledge/admin/rag-docs/{doc_id}`
- `DELETE /api/knowledge/admin/rag-docs/{doc_id}`

### 方式二：导入 PDF / DOCX

适合：指南、科普手册、机构规范、讲义、医院宣教材料。

对应接口：

- `POST /api/knowledge/admin/rag-docs/import`

说明：

- 支持 `.pdf`、`.docx`
- 导入后会提取文本并写入 `rag_knowledge_documents`
- 同时自动同步向量索引

### 方式三：导入示例知识

适合本地联调或演示：

- `POST /api/knowledge/admin/rag-docs/seed-defaults`

---

## 推荐的数据采集与入库流程

如果你要持续扩充 RAG 知识库，建议按下面流程做：

1. **先选可信来源**
   - 国家卫健委、疾控机构、医院官方宣教、临床指南、药品说明书、营养学权威资料
2. **先做筛选和清洗**
   - 去掉广告、版权页、目录、重复页、无关脚注
3. **按主题拆分**
   - 一个文档尽量只讲一个主题，例如：高血压、糖尿病饮食、睡眠管理
4. **补齐元数据**
   - 标题、分类、来源、标签、更新时间
5. **优先导入结构清晰的内容**
   - 段落清楚、语句完整、内容不要太短也不要特别杂
6. **导入后做抽样问答测试**
   - 用真实问题验证召回是否准确，例如“高血压怎么居家监测”
7. **定期更新旧文档**
   - 医疗健康内容具有时效性，过期内容建议停用或替换

---

## 默认说明

- 系统启动时会自动尝试建表和补充部分缺失字段
- 默认管理员账号以 `backend/app/config.py` 中配置为准
- 区块链能力属于可选能力，不影响 AI / RAG 主流程运行

---

## 相关文档

- `docs/ollama-ai-chat-integration.md`：本地大模型、AI 问答与 RAG 改造说明

---

## 常用排查

### 1. AI 没回答或回答为空
检查：

- Ollama 是否启动
- `deepseek-r1:8b` 是否已安装
- `OLLAMA_NUM_PREDICT` 是否过低

### 2. RAG 检索不到内容
检查：

- Qdrant 是否已启动
- `nomic-embed-text` 是否已安装
- 是否已导入 `rag_knowledge_documents`
- 是否已执行索引重建脚本
- 文档是否为启用状态 `is_active=true`

### 3. PDF / DOCX 导入失败
检查：

- 是否已安装 `pypdf`、`python-docx`
- 文件是否损坏
- 文件中是否真实包含可提取文本

---

如果你后续要继续扩展 RAG，建议下一步增加：

- 更细粒度 chunk 策略
- 文档去重
- 文档版本管理
- 召回评估与命中率统计
- 后台批量导入任务队列
