# 求职 AI Copilot

面向应届生的求职协作系统：JD 解析、简历匹配、模拟面试、7 天改进计划，支持评测与 LLM 可观测。

---

## 目录

- [功能模块](#功能模块)
- [环境要求](#环境要求)
- [首次安装](#首次安装)
- [日常启动](#日常启动)
- [PyCharm](#pycharm)
- [常见问题](#常见问题)
- [配置说明](#配置说明)
- [API 列表](#api-列表)

---

## 功能模块

| 模块 | 说明 |
|------|------|
| JD 解析 | 解析职位描述，提取技能与要求 |
| 简历匹配 | 匹配度分析与优化建议 |
| 模拟面试 | 出题、文本/语音作答与评分 |
| 改进计划 | 7 天个性化学习计划 |
| 可观测性 / 评测 | LLM 日志统计、离线评测 |

技术栈：FastAPI + PostgreSQL + Redis + Celery + Vue 3 + Vite。

---

## 环境要求

| 软件 | 版本 | 用途 |
|------|------|------|
| Docker Desktop | 最新 | PostgreSQL、Redis（`docker compose`，无需本机单独安装库） |
| Node.js | 18+ | 前端、`npm run dev` |
| Python | 3.12+ | 创建 `backend/.venv` |
| PyCharm | 可选 | 调试后端（Community 即可） |

`npm run dev` 固定使用 **`backend/.venv`**。若卸载了创建 venv 时的 Python，会报 `No Python at ...Python312...`（退出码 103），需 [重建 venv](#虚拟环境失效-no-python-at-)。其它项目的 `.venv` 不能代替；PyCharm 换解释器也不会自动修好 `npm run dev`。

验证：`docker --version`、`node --version`、`py -3.12 --version`（在新终端、未 activate 任何 venv 时执行）。

---

## 首次安装

```powershell
cd "F:\AI Copilot"
npm install

cd backend
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
py -3.12 -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
copy .env.example .env

cd ..\frontend
npm install

cd ..
docker compose up -d postgres redis
```

`py -3.12` 不可用时，改用本机可用的 Python，例如：`F:\anaconda\python.exe -m venv .venv`。

---

## 日常启动

1. 打开 **Docker Desktop**
2. 项目根目录：输出：`docker compose up -d postgres redis`（`docker ps` 应看到 `job-ai-copilot-postgres`、`job-ai-copilot-redis`）
3. 项目根目录：`npm run dev` → API `8000`、Worker、前端（常见 http://127.0.0.1:5173）

停止：终端 **Ctrl+C**；连库一起停：`docker compose down`。

---

## PyCharm

1. 打开项目根目录；解释器选 **`backend\.venv\Scripts\python.exe`**（须先按上文建好 `.venv`）。
2. **Run → Edit Configurations**，Working directory 均为 `backend`：
   - **API**：Module `uvicorn`，Parameters `app.main:app --reload`
   - **Worker**：Module `celery`，Parameters `-A app.tasks.celery_app worker -l info --pool=solo`（Windows）
3. 先 `docker compose up -d postgres redis`，再运行上述配置；前端：`cd frontend && npm run dev`。

勿与 `npm run dev` 同时起两个 API（端口冲突）。`.env` 在运行配置中加载 `backend/.env`。

---

## 常见问题

### 数据库 / Redis 连不上

`Connection refused`（5432）或 Redis `10061`：先开 Docker Desktop，再执行：

```bash
docker compose up -d postgres redis
```

### 容器名称冲突

```bash
docker compose down
docker rm -f job-ai-copilot-postgres job-ai-copilot-redis
docker compose up -d postgres redis
```

### 虚拟环境失效（No Python at ...）

卸载或移动了创建 `.venv` 时的 Python 会导致 API/Worker 无法启动。重建：

```powershell
cd backend
Remove-Item -Recurse -Force .venv
py -3.12 -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
```

PyCharm：**Settings → Python Interpreter** 重新指向 `backend\.venv\Scripts\python.exe`。

### 前端异常

```powershell
cd frontend
Remove-Item -Recurse -Force node_modules
npm install
npm run dev
```

### 其它

- 全栈 Docker：`docker compose up -d --build`
- 分开启动后端：`cd backend` → `.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload`

---

## 配置说明

`backend/.env`（可由 `.env.example` 复制）：

| 变量 | 说明 | 默认 |
|------|------|------|
| `DATABASE_URL` | PostgreSQL | `postgresql+psycopg2://postgres:postgres@localhost:5432/job_copilot` |
| `PGVECTOR_ENABLED` | pgvector | `false` |
| `LLM_PROVIDER` | mock / openai / compatible | `mock` |
| `LLM_API_KEY` | API 密钥 | 空 |
| `LLM_AUGMENT` | LLM 增强 | `true` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

---

## API 列表

| 接口 | 说明 | 异步 |
|------|------|------|
| `GET /health` | 健康检查 | - |
| `POST /jd/parse` | JD 解析 | 是 |
| `POST /resume/match` | 简历匹配 | 是 |
| `GET /resume/match/history` | 匹配历史 | - |
| `POST /interview/session` | 创建面试 | 是 |
| `POST /interview/{id}/answer` | 文本作答 | 是 |
| `POST /interview/{id}/answer/audio` | 语音作答 | 是 |
| `GET /interview/{id}/report` | 面试报告 | - |
| `POST /plan/generate` | 改进计划 | 是 |
| `GET /plan/latest` | 最新计划 | - |
| `GET /llm/logs` | LLM 日志 | - |
| `GET /llm/stats` | LLM 统计 | - |
| `POST /admin/backfill` | 向量回填 | - |
| `GET /tasks/{task_id}` | 任务状态 | - |

---

## 许可证

MIT License
