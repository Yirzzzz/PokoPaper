# Pokomon

Pokomon is a Pokemon-themed paper companion agent for beginners. This repository contains:

- `apps/web`: Next.js frontend
- `apps/api`: FastAPI backend
- `infra/compose`: local infrastructure for PostgreSQL, Redis, and Qdrant

## 项目简介

Pokomon 是一个面向论文初学者的 Paper Companion Agent。用户上传论文后，系统会围绕“快速理解论文”这个目标，提供结构化概览、持续追问、引用定位、补充阅读建议和阅读记忆，而不是停留在普通 PDF Chat。

当前版本优先支持文本型学术 PDF：

- 支持可复制文本的论文 PDF
- 支持论文上传、文本抽取、section/chunk 初步切分
- 支持概览生成、问答、citation 展示
- 暂不支持扫描版 PDF 和 OCR 流程

## 技术栈与选型理由

### 前端

- `Next.js (App Router)`
  - 用于构建论文工作台、问答页、阅读记忆页等多页面 AI 产品界面
  - 适合服务端拉取数据和前端交互混合场景，方便后续扩展鉴权、SSR、流式输出

- `TypeScript`
  - 保证前后端接口和组件状态更稳定
  - 对聊天消息、citation、overview、memory 这类结构化对象更友好

- `Tailwind CSS`
  - 用于快速搭建深色三栏 AI SaaS 风格界面
  - 适合高频迭代卡片化布局和主题化样式

- `react-markdown + remark-math + rehype-katex`
  - 用于渲染论文解读中的 Markdown 和 LaTeX
  - 这是论文阅读场景的核心能力，不只是普通文本聊天

- `Zustand`
  - 用于管理当前论文、会话状态、后续模型选择等轻量全局状态
  - 相比更重的状态管理方案更适合 MVP

### 后端

- `FastAPI`
  - 用于构建上传、解析、问答、memory、recommendation 等 API
  - 开发效率高，适合 AI 应用的快速原型和结构化接口设计

- `Pydantic`
  - 用于约束 API schema、overview、citation、chat message 等核心数据结构
  - 保证前后端通信稳定，便于后续接入真实数据库和异步任务

- `OpenAI Python SDK（兼容接口）`
  - 用于对接 ModelScope / DashScope 这类 OpenAI-compatible 推理服务
  - 通过统一适配层支持多模型切换，而不把模型提供商写死在业务代码里

### 存储与检索

- `PostgreSQL`
  - 作为业务主存储，适合保存论文元数据、解析结果、聊天记录、阅读记忆
  - 当前项目已预留 PostgreSQL repository，可在本地 JSON 与 PostgreSQL 之间切换

- `Redis`
  - 预留给 session memory、任务状态缓存、后续异步任务队列
  - MVP 阶段未深度使用，但已纳入整体架构

- `Qdrant`
  - 预留给 chunk embedding 和向量检索
  - 这是项目从“结构化问答”升级到“真实 RAG 检索”的关键组件

### 工程与架构

- `Monorepo`
  - 将前端、后端、基础设施、文档放在同一仓库
  - 便于统一维护 API 契约、部署说明和实验记录

- `Repository Pattern`
  - 当前实现了 `local JSON store` 和 `PostgreSQL store` 两套仓储
  - 这样能先快速落地 MVP，再逐步升级到正式持久化，而不重写上层服务

- `Single Agent + Tool-ready Architecture`
  - MVP 阶段优先采用单主 Agent 编排
  - 避免过早设计复杂多 Agent，同时为后续 retrieval routing、memory injection、recommendation tool 留好扩展边界

## 为什么这个技术栈适合这个项目

这个项目不是单纯的“上传 PDF 然后问答”，而是一个同时包含产品体验、结构化解析、RAG、记忆系统和模型编排的 AI 应用。因此技术选型重点不是某个单点技术最强，而是：

- 前端要足够快地迭代 AI SaaS 工作台体验
- 后端要能承载 ingestion、问答、citation、memory 等模块化能力
- 存储层要兼顾 MVP 快速落地与后续真实 RAG 升级
- 模型层要支持多 provider 切换，避免供应商绑定

基于这个目标，`Next.js + FastAPI + PostgreSQL + Redis + Qdrant` 是一套足够稳、足够常见、也足够适合简历表达和后续演进的技术组合。

## 简历项目描述

下面这段可以直接放进简历，你可以按“项目名称 + 技术栈 + 项目描述 + 个人贡献/亮点”的格式使用。

### 项目名称

`Pokomon | 宝可梦主题论文辅读智能体`

### 技术栈

`Next.js, TypeScript, Tailwind CSS, FastAPI, Pydantic, PostgreSQL, Redis, Qdrant, OpenAI-Compatible LLM APIs`

### 项目描述

面向论文初学者设计并实现论文辅读智能体 Web 项目，支持文本型论文 PDF 上传、结构化概览生成、基于引用定位的连续问答、补充阅读建议与阅读记忆管理，帮助用户从“能问”提升到“真正理解论文”。

### 简历亮点版

- 从 0 到 1 设计并实现论文陪读智能体 Web 系统，完成前后端一体化架构搭建，支持论文上传、解析、概览生成、问答与 citation 展示闭环
- 设计可演进的 RAG 架构，围绕论文场景拆分 ingestion、chunking、query understanding、citation grounding、answer synthesis 等模块
- 实现文本型 PDF ingestion pipeline，完成论文文本抽取、section 切分、chunk 生成与结构化 overview 产出
- 设计并实现阅读记忆机制，区分 session memory、用户偏好与论文阅读 episode，为后续个性化解释和推荐阅读打下基础
- 设计多模型可切换的 LLM 接入层，兼容 ModelScope / DashScope 等 OpenAI-compatible 接口，支持前端动态选择模型
- 采用 repository pattern 统一本地 JSON 与 PostgreSQL 持久化实现，降低 MVP 到正式版本的迁移成本

### 面试表达版

如果你要在面试里展开，可以这样讲：

“我做了一个面向论文初学者的 Paper Companion Agent。它不是普通 PDF Chat，而是把论文理解拆成了上传解析、结构化概览、问题类型感知问答、citation 定位、补充阅读推荐和阅读记忆几个模块。技术上我采用 Next.js + FastAPI 做前后端，后端按可演进的 RAG 架构去拆服务边界，并且预留了 PostgreSQL、Redis、Qdrant 和多模型 provider 的扩展能力。MVP 阶段先打通文本型 PDF 的上传、解析和问答闭环，后续可以继续升级 OCR、向量检索和异步任务。”

## MVP scope

- Upload a paper PDF
- Persist the uploaded PDF to local storage
- Extract text and generate first-pass structured paper data
- Show a paper overview
- Ask follow-up questions with citations
- Surface lightweight reading memory and recommendations

## Current persistence mode

The backend now uses a local JSON repository under `storage/` for first-pass persistence:

- `storage/papers/`: uploaded PDFs
- `storage/db/store.json`: papers, jobs, overview, memory, chat state

This preserves the service boundaries so PostgreSQL and Qdrant can replace the local store later without changing the API surface.

To switch to PostgreSQL metadata storage:

1. Start infra with `make infra-up`
2. Set `USE_MOCK_SERVICES=false`
3. Ensure `POSTGRES_URL` points to the running database

File blobs still live in `storage/papers/` in the current version.

## Local development

1. Copy `.env.example` to `.env`.
2. Start infra with Docker Compose.
3. Start `apps/api`.
4. Start `apps/web`.

Detailed commands are provided in the app-level READMEs and `Makefile`.

## Deployment

The current repository is ready for a pragmatic two-service deployment:

- `apps/api`: FastAPI backend
- `apps/web`: Next.js frontend
- Managed or self-hosted infra:
  - PostgreSQL
  - Redis
  - Qdrant

### 1. Deployment modes

#### Mode A: Local-first MVP

Use this if you want the fastest way to run the project end to end.

- Set `USE_MOCK_SERVICES=true`
- Uploaded PDFs are stored in `storage/papers/`
- Parsed metadata is stored in `storage/db/store.json`
- PostgreSQL, Redis, and Qdrant can stay unused

This mode is useful for UI iteration and ingestion workflow debugging.

#### Mode B: Database-backed MVP

Use this when you want stable persistence and a deployment shape closer to production.

- Set `USE_MOCK_SERVICES=false`
- Metadata is stored in PostgreSQL
- Uploaded PDFs still live on local disk in `storage/papers/`
- Redis and Qdrant are reserved for the next retrieval upgrade stage

### 2. Required environment variables

Copy `.env.example` to `.env` and adjust these values:

```bash
NEXT_PUBLIC_API_BASE_URL=http://your-api-host:8000/api/v1
API_HOST=0.0.0.0
API_PORT=8000
API_ENV=production

POSTGRES_URL=postgresql://postgres:postgres@your-postgres-host:5432/pokomon
REDIS_URL=redis://your-redis-host:6379/0
QDRANT_URL=http://your-qdrant-host:6333

STORAGE_DIR=./storage
USE_MOCK_SERVICES=false
DATABASE_ECHO=false
MODELSCOPE_BASE_URL=https://api-inference.modelscope.cn/v1
MODELSCOPE_API_KEY=your-modelscope-token
MODELSCOPE_MODEL=Qwen/Qwen3-32B
MODELSCOPE_ENABLE_THINKING=false
MODELSCOPE_THINKING_BUDGET=

DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_API_KEY=your-dashscope-key
DASHSCOPE_MODEL=ZhipuAI/GLM-4.7
```

### 3. Local deployment with Docker infra

This is the recommended first deployment path for a single machine or a small VPS.

#### Step 1: Start infrastructure

```bash
make infra-up
```

This starts:

- PostgreSQL on `localhost:5432`
- Redis on `localhost:6379`
- Qdrant on `localhost:6333`

#### Step 2: Start backend

```bash
cd apps/api
pip install -e .
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

If `USE_MOCK_SERVICES=false`, the backend will create database tables on startup.

#### Step 3: Start frontend

```bash
cd apps/web
npm install
npm run build
npm run start
```

Frontend default port:

- `3000`

Backend default port:

- `8000`

### 4. Production deployment recommendation

For the current codebase, a simple and reliable production topology is:

1. Deploy `apps/api` as one service.
2. Deploy `apps/web` as one service.
3. Use managed PostgreSQL.
4. Add persistent disk or object storage for uploaded PDFs.
5. Put Nginx or a cloud load balancer in front.

Suggested mapping:

- Frontend:
  - Vercel, Coolify, Railway, or a Dockerized Node host
- Backend:
  - Railway, Render, Fly.io, ECS, or a Docker VM
- Database:
  - Neon, RDS, Supabase Postgres, or self-hosted Postgres

### 5. Reverse proxy example

If you deploy on one server with Nginx:

- `https://your-domain.com` -> Next.js frontend
- `https://your-domain.com/api/` -> FastAPI backend

In that setup:

```bash
NEXT_PUBLIC_API_BASE_URL=https://your-domain.com/api/v1
```

### 6. Persistence and storage notes

Current storage behavior:

- PDF files are stored on local disk
- With `USE_MOCK_SERVICES=true`, metadata is stored in local JSON
- With `USE_MOCK_SERVICES=false`, metadata is stored in PostgreSQL

For real production, you should plan the following upgrades:

- Replace local PDF storage with S3, R2, or MinIO
- Add database migrations with Alembic
- Add background jobs for ingestion
- Add Qdrant vector indexing during ingestion

### 6.1 Optional model providers

The chat panel can expose multiple optional models from environment configuration.

Current supported provider slots:

- `ModelScope`
- `DashScope`

Frontend will call `GET /api/v1/chat/models` and show only enabled models.
If no model key is configured, the backend falls back to the internal heuristic answer path.
The model `id` is now generated from the actual provider + model name, for example `modelscope:qwen:qwen3-32b`.

### 7. Health checks

Useful endpoints after deployment:

```bash
GET /           # root metadata
GET /api/v1/health
GET /api/v1/papers
```

Example:

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/papers
```

### 7.1 Verify external model usage

After configuring `MODELSCOPE_*` or `DASHSCOPE_*` and restarting the backend:

1. Check model availability:

```bash
curl http://localhost:8000/api/v1/chat/models
```

2. Upload a text-based PDF from the homepage.
3. Watch backend logs for lines such as:

```text
llm.analysis request: ...
llm.analysis success: ...
chat.answer: ... source=llm
```

If you instead see `source=heuristic_fallback`, the request did not hit the external model successfully.

### 8. Current deployment limitations

This version is deployable, but not yet fully production-grade. Main gaps:

- No authentication
- No Alembic migrations
- No async job queue for ingestion
- No object storage for PDFs
- No real Qdrant indexing yet
- No production Dockerfiles for app services yet

### 9. Recommended next deployment upgrades

If you want this project to move from MVP to production-ready, the next steps should be:

1. Add Dockerfiles for `apps/api` and `apps/web`
2. Add Alembic migrations
3. Move file storage to S3-compatible storage
4. Add Celery or Dramatiq for ingestion jobs
5. Connect Qdrant indexing and retrieval
6. Add auth and multi-user isolation
