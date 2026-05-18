# 求职 AI Copilot

面向应届生的求职协作系统：**JD 解析 → 简历匹配 → 模拟面试 → 7 天训练计划**，支持 LLM 增强、语音面试、历史记录与调用可观测。适合作为**求职作品集**本地 MVP 演示。

---

## 作品集演示（3 分钟）

| 步骤 | 页面 | 说明 |
|------|------|------|
| 1 | JD 解析 | 粘贴职位描述，得到结构化技能与关键词 |
| 2 | 简历匹配 | 匹配分、差距分析、改写建议 |
| 3 | 模拟面试 | 文本/语音作答，生成评分与总结 |
| 4 | 训练计划 | 基于面试结果生成 7 天计划 |
| — | [我的记录](/history) | 按邮箱查看匹配、面试、计划历史；支持关键字模糊搜索与分页（详见 [我的记录](#我的记录)） |

**访问地址**（`npm run dev` 后）：

- 前端：http://127.0.0.1:5173  

**演示说明**：当前为 MVP，**无登录**；各页填写**同一邮箱**即可在「我的记录」聚合数据。

**技术亮点**：FastAPI + Celery 异步 · Vue3 · Docker（PostgreSQL/Redis）· Knife4j/Scalar API 文档 · 规则引擎 + LLM 可降级 Mock · 语音 ASR + ffmpeg · 历史分页 + 模糊搜索 · `/llm/stats` 可观测。

---

## 目录

- [环境要求](#环境要求)
- [首次安装](#首次安装)
- [日常启动](#日常启动)
- [我的记录](#我的记录)
- [API 文档（Knife4j / Scalar）](#api-文档knife4j--scalar)
- [PyCharm](#pycharm)
- [配置与密钥](#配置与密钥)
- [常见问题](#常见问题)
- [API 列表](#api-列表)

---

## 环境要求

| 软件 | 版本 | 用途 |
|------|------|------|
| Docker Desktop | 最新 | PostgreSQL、Redis |
| Node.js | 18+ | 前端、`npm run dev` |
| Python | 3.12+ | `backend/.venv` |
| PyCharm | 可选 | 调试后端 |

`npm run dev` 使用 **`backend/.venv`**。若卸载了创建 venv 时的 Python，会报 `No Python at ...Python312...`，见 [虚拟环境失效](#虚拟环境失效)。

**密钥与 Git**：`backend/.env` 含 API Key，已被 `.gitignore` 忽略，**不会**随 `git push` 上传；克隆后请 `copy .env.example .env` 自填。

验证：`docker --version`、`node --version`、`py -3.12 --version`（新终端、勿 activate 旧 venv）。

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

# Knife4j 文档 UI（首次必做；webjars 未提交 Git，需本机拉取）
powershell -ExecutionPolicy Bypass -File backend\scripts\fetch_knife4j_ui.ps1
```

---

## 日常启动

1. 打开 **Docker Desktop**
2. `docker compose up -d postgres redis`
3. `npm run dev`
   - 前端：http://127.0.0.1:5173  
   - API 文档（推荐）：http://127.0.0.1:8000/doc.html  

停止：**Ctrl+C**；停库：`docker compose down`。

---

## 我的记录

按邮箱聚合**简历匹配**、**模拟面试**、**训练计划**三块历史，支持 PostgreSQL 模糊搜索与分页。页面路由：`/history`（顶栏「我的记录」），实现见 `frontend/src/pages/History.vue`。

### 页面交互

| 模块 | 搜索范围（`ILIKE`） | 默认每页 |
|------|---------------------|----------|
| 简历匹配 | 公司、岗位 | 10 |
| 模拟面试 | 公司、岗位、状态 | 10 |
| 训练计划 | 公司、岗位、计划 ID、会话 ID（JOIN 面试/JD） | 10 |

- 顶部输入邮箱并点击「查询」后，三块数据**并行**加载，各块 `page` 重置为 1。
- 各块有**独立**搜索框；输入关键字 **300ms 防抖** 后自动查询，并将该块重置到第 1 页。
- 翻页或修改每页条数（10 / 20 / 50）时，仅请求**对应块**接口。
- 卡片标题旁「共 N 条」来自接口字段 `total`，不是当前页 `items` 条数。

### 分页 API

三条接口共用 Query 参数：

| 参数 | 必填 | 默认 | 说明 |
|------|------|------|------|
| `user_email` | 是 | — | 用户邮箱 |
| `page` | 否 | 1 | ≥ 1 |
| `page_size` | 否 | 10 | 1–50 |
| `keyword` | 否 | — | 空则不过滤；多字段 OR 模糊匹配 |

| 接口 | 说明 |
|------|------|
| `GET /user/history/matches` | 简历匹配历史 |
| `GET /user/history/interviews` | 模拟面试历史 |
| `GET /user/history/plans` | 训练计划历史 |

响应体（三块结构相同，`items` 元素类型不同）：

```json
{
  "items": [],
  "total": 15,
  "page": 1,
  "page_size": 10
}
```

示例：

```
GET /user/history/matches?user_email=demo@example.com&page=1&page_size=10&keyword=阿里
```

**兼容接口**：`GET /user/history` 仍返回三块首屏摘要（各块 `page_size=20`）。当前前端以三条分页接口为准。

### 前端中文分页

`frontend/src/main.js` 中为 Element Plus 注册了 `element-plus/es/locale/lang/zh-cn`，分页器显示「共 N 条」「N 条/页」等中文文案，全站 Element Plus 组件同步生效。

### 演示步骤

1. 在 JD 解析、简历匹配、模拟面试、训练计划等页使用**同一邮箱**完成操作。
2. 打开 http://127.0.0.1:5173/history ，输入该邮箱并点击「查询」。
3. 在任一块搜索框输入公司名（如「阿里」），确认列表与「共 N 条」随关键字变化。
4. 翻页或切换每页条数，在浏览器网络面板中确认仅请求对应块的 API，且 `page` / `page_size` 正确。

---

## API 文档（Knife4j / Scalar）

本项目为 **FastAPI**，无 Java 版 Knife4j Starter，采用 **挂载 Knife4j 官方静态 UI** + **Scalar 备用** 的方式提供接口文档。

### 访问地址

| 地址 | 说明 |
|------|------|
| http://127.0.0.1:8000/doc.html | **Knife4j**（推荐，中文界面、分组清晰） |
| http://127.0.0.1:8000/scalar | **Scalar** 备用（`scalar-fastapi`，Knife4j 资源缺失时可用） |
| http://127.0.0.1:8000/docs | FastAPI 自带 Swagger UI |
| http://127.0.0.1:8000/redoc | ReDoc |
| http://127.0.0.1:8000/openapi.json | OpenAPI 3 规范 JSON |

### 实现说明

| 项 | 路径 / 说明 |
|----|-------------|
| 静态资源 | `backend/app/static/knife4j/`（`doc.html`、`webjars/`、`group.json`） |
| 拉取脚本 | `backend/scripts/fetch_knife4j_ui.ps1`（从 Maven 下载 `knife4j-openapi3-ui` 4.5.0） |
| 后端注册 | `backend/app/main.py`：挂载 `/doc.html`、`/webjars`，并提供 `/v3/api-docs/swagger-config` 指向 `/openapi.json` |
| Python 依赖 | `scalar-fastapi`（见 `backend/requirements.txt`） |
| 接口分组 | `routes.py` 中为接口配置了中文 `tags` / `summary`（系统、JD、简历、面试、计划、用户、LLM、管理） |

### 首次使用 Knife4j

```powershell
# 在项目根目录执行（需联网）
powershell -ExecutionPolicy Bypass -File backend\scripts\fetch_knife4j_ui.ps1

# 重启 API 后访问
# http://127.0.0.1:8000/doc.html
```

`webjars/` 体积较大，已在 `.gitignore` 中忽略；**新 clone 仓库后需执行上述脚本**。若 `/doc.html` 空白或样式丢失，多半是未拉取 `webjars`，重新执行脚本即可。

### 在文档里调试接口

- 无需登录；先调 `GET /health` 确认服务正常。
- 依赖数据库的接口需 Docker 中 Postgres/Redis 已启动。
- 带 `async=true` 的接口返回 `task_id`，可用 `GET /tasks/{task_id}` 查结果。

---

## PyCharm

1. 解释器：`backend\.venv\Scripts\python.exe`
2. Working directory = `backend`：**uvicorn** `app.main:app --reload`；**celery** `-A app.tasks.celery_app worker -l info --pool=solo`
3. 先起 Docker，再跑 API/Worker；前端：`cd frontend && npm run dev`
4. 文档：启动 API 后浏览器打开 http://127.0.0.1:8000/doc.html

---

## 配置与密钥

复制 `backend/.env.example` → `backend/.env`（**勿提交 `.env`**）。

| 变量 | 说明 |
|------|------|
| `LLM_PROVIDER` / `LLM_API_KEY` / `LLM_BASE_URL` | 大模型（`mock` 可无 Key 演示） |
| `ASR_PROVIDER` / `ASR_API_KEY` / `ASR_APP_KEY` | 语音面试（阿里云等） |
| `FFMPEG_PATH` | Windows 语音转写需 ffmpeg 绝对路径 |
| `DATABASE_URL` | PostgreSQL |

---

## 常见问题

### 数据库 / Redis 连不上

```bash
docker compose up -d postgres redis
```

### 虚拟环境失效

```powershell
cd backend
Remove-Item -Recurse -Force .venv
py -3.12 -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
```

PyCharm 中重新选择 `backend\.venv\Scripts\python.exe`。

### Knife4j 打不开或页面空白

1. 确认已执行：`backend\scripts\fetch_knife4j_ui.ps1`
2. 确认存在目录：`backend\app\static\knife4j\webjars\`
3. 重启 API 后访问 http://127.0.0.1:8000/doc.html
4. 仍不行时使用备用：http://127.0.0.1:8000/scalar 或 http://127.0.0.1:8000/docs

### 前端异常

```powershell
cd frontend
Remove-Item -Recurse -Force node_modules
npm install
```

---

## API 列表

OpenAPI 规范由 FastAPI 自动生成；在线调试推荐使用 [Knife4j](/doc.html) 页面。

| 接口 | 分组 | 说明 |
|------|------|------|
| `GET /health` | 系统 | 健康检查 |
| `GET /tasks/{task_id}` | 系统 | 异步任务状态 |
| `POST /jd/parse` | JD | 解析职位描述 |
| `POST /resume/match` | 简历 | 简历与 JD 匹配 |
| `GET /resume/match/history` | 用户 | 匹配历史（`user_email`） |
| `GET /user/history` | 用户 | 匹配 + 面试 + 计划汇总（兼容，各块首屏；详见 [我的记录](#我的记录)） |
| `GET /user/history/matches` | 用户 | 匹配历史分页（详见 [我的记录](#我的记录)） |
| `GET /user/history/interviews` | 用户 | 面试历史分页（详见 [我的记录](#我的记录)） |
| `GET /user/history/plans` | 用户 | 计划历史分页（详见 [我的记录](#我的记录)） |
| `POST /interview/session` | 面试 | 创建面试会话 |
| `POST /interview/{id}/answer` | 面试 | 文本作答 |
| `POST /interview/{id}/answer/audio` | 面试 | 语音作答 |
| `GET /interview/{id}/report` | 面试 | 面试报告 |
| `POST /plan/generate` | 计划 | 生成 7 天计划 |
| `GET /plan/latest` | 计划 | 最新计划 |
| `GET /llm/logs` | LLM | 调用日志 |
| `GET /llm/stats` | LLM | 调用统计 |
| `POST /admin/backfill` | 管理 | 向量回填 |

---

## 许可证

MIT License
