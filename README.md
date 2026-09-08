# AI Knowledge Backend

基于 **FastAPI** 构建的 AI 知识库后端系统，集成 **JWT、MySQL、Redis、Qdrant、BGE Embedding 与 Qwen LLM**，实现用户认证、文档知识库管理、聊天记录持久化以及基于 RAG（Retrieval-Augmented Generation）的智能问答。

项目重点不仅是调用大语言模型，而是实现一套较完整的 **Python 后端 + RAG 服务链路**。

---

## Features

### 用户与认证

- 用户注册与登录
- JWT 身份认证
- Bearer Token 接口鉴权
- 用户聊天记录隔离

### RAG 问答

- BGE 中文文本向量化
- Qdrant 向量检索
- Top-K 语义召回
- Qwen 大模型答案生成
- 返回知识来源
- Redis 问答缓存
- 用户级缓存隔离

### 文档知识库

- TXT 文档上传
- Markdown 文档上传
- PDF 文本解析
- 文档自动切块
- Embedding 向量化
- Qdrant 向量索引
- 同名文档重新上传自动更新索引
- 文档列表查询
- 文档及对应向量删除
- JWT 文档接口鉴权

### 数据持久化

- MySQL 用户数据存储
- MySQL 聊天记录存储
- 聊天历史分页查询
- 用户级聊天记录删除

---

## Tech Stack

| Category | Technology |
| --- | --- |
| Backend | Python, FastAPI |
| ORM | SQLAlchemy |
| Database | MySQL |
| Cache | Redis |
| Vector Database | Qdrant |
| Embedding | BAAI/bge-small-zh-v1.5 |
| LLM | Qwen |
| LLM API | Alibaba Cloud DashScope |
| Authentication | JWT / HTTP Bearer |
| Document Parsing | PyPDF |
| Infrastructure | Docker Compose |
| API Documentation | Swagger / OpenAPI |

---

## Architecture

```text
                         ┌───────────────┐
                         │    Client     │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │    FastAPI    │
                         └───────┬───────┘
                                 │
             ┌───────────────────┼───────────────────┐
             │                   │                   │
             ▼                   ▼                   ▼
      ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
      │    MySQL    │     │    Redis    │     │ RAG Service │
      │ User / Chat │     │    Cache    │     └──────┬──────┘
      └─────────────┘     └─────────────┘            │
                                             ┌───────┴───────┐
                                             ▼               ▼
                                      ┌─────────────┐  ┌───────────┐
                                      │   Qdrant    │  │ Qwen LLM  │
                                      │ Vector DB   │  │           │
                                      └─────────────┘  └───────────┘
```

---

## RAG Workflow

```text
User Question
      │
      ▼
BGE Embedding
      │
      ▼
Qdrant Vector Search
      │
      ▼
Top-K Relevant Chunks
      │
      ▼
Build Context Prompt
      │
      ▼
Qwen LLM
      │
      ▼
Generated Answer + Sources
```

文档进入知识库时：

```text
Upload Document
      │
      ▼
Extract Text
      │
      ▼
Text Chunking
      │
      ▼
BGE Embedding
      │
      ▼
Qdrant Vector Index
      │
      ▼
Available for RAG Search
```

---

## Project Structure

```text
ai-knowledge-backend/
│
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── chat.py
│   │       ├── documents.py
│   │       └── health.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   │
│   ├── models/
│   │   ├── chat_message.py
│   │   └── user.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   └── chat.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── embedding_service.py
│   │   ├── llm_service.py
│   │   ├── qdrant_service.py
│   │   └── rag_service.py
│   │
│   ├── main.py
│   └── redis_client.py
│
├── data/
│   ├── knowledge.txt
│   └── uploads/
│
├── scripts/
│   ├── index_knowledge.py
│   ├── search_knowledge.py
│   ├── test_embedding.py
│   ├── test_llm.py
│   ├── test_qdrant.py
│   └── test_rag.py
│
├── tests/
│   └── test_health.py
│
├── .dockerignore
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Getting Started

### 1. Clone Repository

```bash
git clone https://github.com/qiu251091-svg/ai-knowledge-backend.git
cd ai-knowledge-backend
```

### 2. Create Virtual Environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

然后修改 `.env`：

```env
JWT_SECRET=your-jwt-secret

DATABASE_URL=mysql+pymysql://root:your-password@localhost:3306/ai_knowledge

REDIS_URL=redis://localhost:6379/0

QDRANT_URL=http://localhost:6333

DASHSCOPE_API_KEY=your-dashscope-api-key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
```

> `.env` 包含密码和 API Key，已通过 `.gitignore` 排除，请勿提交到 Git 仓库。

---

## Start Infrastructure

Redis 和 Qdrant 使用 Docker Compose 管理：

```bash
docker compose up -d
```

查看运行状态：

```bash
docker compose ps
```

正常情况下应包含：

```text
ai-redis
ai-qdrant
```

Qdrant Dashboard：

```text
http://localhost:6333/dashboard
```

---

## MySQL

本地 MySQL 创建数据库：

```sql
CREATE DATABASE ai_knowledge;
```

并确保 `.env` 中的 `DATABASE_URL` 与本地 MySQL 配置一致。

---

## Initialize Knowledge Base

将基础知识写入 Qdrant：

```bash
python -m scripts.index_knowledge
```

可通过以下脚本测试语义检索：

```bash
python -m scripts.search_knowledge
```

---

## Run Application

```bash
uvicorn app.main:app --reload
```

服务默认运行于：

```text
http://127.0.0.1:8000
```

Swagger API 文档：

```text
http://127.0.0.1:8000/docs
```

---

## API Overview

### Authentication

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录并获取 JWT |

### Chat

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/chat` | RAG 智能问答 |
| GET | `/api/chat/history` | 分页查询当前用户聊天记录 |
| DELETE | `/api/chat/{message_id}` | 删除当前用户聊天记录 |

### Documents

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/documents/upload` | 上传并索引文档 |
| GET | `/api/documents` | 查询知识库文档 |
| DELETE | `/api/documents/{filename}` | 删除文档及向量 |

文档相关接口需要 JWT 身份认证。

---

## Document Processing

目前支持：

```text
.txt
.md
.pdf
```

默认切块参数：

```text
chunk_size = 500
overlap = 100
```

处理过程：

1. 读取文档内容
2. 提取文本
3. 按固定长度进行重叠切块
4. 使用 BGE 生成 512 维文本向量
5. 将向量及文本 metadata 写入 Qdrant
6. RAG 查询时进行 Top-K 相似度检索

对于同名文档重新上传，系统会删除旧向量后重新建立索引，避免重复数据。

> PDF 当前仅支持包含文本层的文件，暂不支持扫描图片型 PDF OCR。

---

## Redis Cache

系统对问答结果进行 Redis 缓存，以减少重复向量检索和 LLM API 调用。

缓存 TTL：

```text
300 seconds
```

缓存按照用户进行隔离：

```text
chat:<username>:<question>
```

---

## Security

目前已实现：

- JWT 身份认证
- HTTP Bearer Token
- 用户聊天记录隔离
- 文档接口鉴权
- `.env` 敏感配置隔离
- 密码哈希存储

---

## Future Improvements

- 文档上传大小限制
- 文件名与路径安全校验
- 用户级独立知识库
- Redis 知识库版本控制与缓存失效
- RAG 相似度阈值过滤
- Hybrid Search
- Alembic 数据库迁移
- 完善自动化 API 测试
- OCR 扫描 PDF 支持
- 完整服务容器化部署

---

## License

See [LICENSE](LICENSE).