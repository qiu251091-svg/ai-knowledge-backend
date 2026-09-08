# AI Knowledge Backend

基于 FastAPI 构建的 AI 知识库后端系统，集成 JWT 用户认证、MySQL 数据持久化、Redis 缓存、Qdrant 向量数据库、BGE Embedding 和 Qwen 大语言模型，实现基于用户文档的 RAG（Retrieval-Augmented Generation）问答。

## Features

- 用户注册与登录
- JWT 身份认证
- MySQL 用户及聊天记录持久化
- Redis 问答缓存
- Qdrant 向量数据库
- BGE 中文文本向量化
- Qwen 大模型生成答案
- RAG 检索增强生成
- TXT / Markdown / PDF 文档上传
- 文档自动切块与向量化
- 同名文档重新上传自动更新向量
- 文档列表查询
- 文档删除及向量同步删除
- Swagger API 在线调试

## Tech Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic

### Database

- MySQL
- Redis
- Qdrant

### AI / RAG

- BAAI/bge-small-zh-v1.5
- Sentence Transformers
- Qwen
- Alibaba Cloud DashScope
- OpenAI Compatible API

### Deployment

- Docker
- Docker Compose
- Uvicorn

## Project Structure

```text
ai-knowledge-backend/
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
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md

RAG Workflow
User Question
      ↓
Text Embedding
      ↓
Qdrant Semantic Search
      ↓
Retrieve Relevant Knowledge
      ↓
Build Prompt
      ↓
Qwen LLM
      ↓
Generated Answer


文档上传后的处理流程：
Upload Document
      ↓
Extract Text
      ↓
Text Chunking
      ↓
BGE Embedding
      ↓
Store Vectors in Qdrant
      ↓
Available for RAG Search
Environment Variables

复制：

.env.example
创建：

.env

配置以下环境变量：

JWT_SECRET=your-jwt-secret

DATABASE_URL=mysql+pymysql://root:your-password@localhost:3306/ai_knowledge

REDIS_URL=redis://localhost:6379/0

QDRANT_URL=http://localhost:6333

DASHSCOPE_API_KEY=your-dashscope-api-key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus

Installation
1. Clone Project
git clone <your-repository-url>
cd ai-knowledge-backend
2. Create Virtual Environment

Windows:

python -m venv .venv
.venv\Scripts\Activate.ps1
3. Install Dependencies
pip install -r requirements.txt
Start Infrastructure

启动 Redis 和 Qdrant。

如果已经创建 Docker 容器：

docker start ai-redis
docker start ai-qdrant

确认容器运行：

docker ps

Qdrant Dashboard：

http://localhost:6333/dashboard

MySQL 中创建数据库：

CREATE DATABASE ai_knowledge;
Run Application
uvicorn app.main:app --reload

启动成功后访问：

http://127.0.0.1:8000/docs

即可使用 Swagger UI 调试 API。

Main APIs
Authentication
POST /api/auth/register
POST /api/auth/login
Chat
POST   /api/chat
GET    /api/chat/history
DELETE /api/chat/{message_id}
Documents
POST   /api/documents/upload
GET    /api/documents
DELETE /api/documents/{filename}
Supported Documents

目前支持：

.txt
.md
.pdf

PDF 需要包含可提取的文本层,扫描版 PDF 暂不支持 OCR。

Document Chunking

上传文档后，系统使用固定长度切块：

chunk_size = 500
overlap = 100

每个 Chunk 会通过 BGE 模型转换为向量，并存入 Qdrant。

Redis Cache

系统对重复问题进行 Redis 缓存：

chat:<question>

默认缓存时间：

300 seconds

减少重复向量检索和大模型 API 调用。

Future Improvements
RAG 相似度阈值过滤
RAG / LLM 混合问答
用户级知识库隔离
Redis 缓存版本控制
文档上传大小限制
文件名安全校验
OCR 扫描 PDF 支持
Alembic 数据库迁移
Docker Compose 一键启动完整服务
自动化 API 测试