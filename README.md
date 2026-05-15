# 求职 AI Copilot

面向应届生的求职协作系统：**JD 解析 → 简历匹配 → 模拟面试 → 7 天训练计划**，支持 LLM 增强、语音面试与调用可观测。适合作为**求职作品集**本地 MVP 演示。

---

## 作品集演示（3 分钟）

| 步骤 | 页面 | 说明 |
|------|------|------|
| 1 | JD 解析 | 粘贴职位描述，得到结构化技能与关键词 |
| 2 | 简历匹配 | 匹配分、差距分析、改写建议 |
| 3 | 模拟面试 | 文本/语音作答，生成评分与总结 |
| 4 | 训练计划 | 基于面试结果生成 7 天计划 |
| — | [我的记录](/history) | 按邮箱查看匹配、面试、计划历史 |

**访问地址**（`npm run dev` 后）：

- 前端：http://127.0.0.1:5173  
- API 文档：http://127.0.0.1:8000/docs  

**演示账号说明**：当前为 MVP，**无登录**；各页填写同一邮箱即可在「我的记录」聚合数据。上线计划：JWT 鉴权。

**技术亮点**：FastAPI + Celery 异步 · Vue3 · Docker（PostgreSQL/Redis）· 规则引擎 + LLM 可降级 Mock · 语音 ASR + ffmpeg · `/llm/stats` 可观测。

---

## 目录

- [环境要求](#环境要求)
- [首次安装](#首次安装)
- [日常启动](#日常启动)
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

`npm run dev` 使用 **`backend/.venv`**。若卸载了创建 venv 时的 Python，会报 `No Python at ...Python312...`，见 [虚拟环境失效](#虚拟环境失效)。**`backend/.env` 含密钥，已被 `.gitignore` 忽略，不会随 `git push` 上传**；克隆后请 `copy .env.example .env` 自填。

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
```

---

## 日常启动

1. 打开 **Docker Desktop**
2. `docker compose up -d postgres redis`
3. `npm run dev` → 浏览器打开 http://127.0.0.1:5173

停止：**Ctrl+C**；停库：`docker compose down`。

---

## PyCharm

1. 解释器：`backend\.venv\Scripts\python.exe`
2. Working directory = `backend`：**uvicorn** `app.main:app --reload`；**celery** `-A app.tasks.celery_app worker -l info --pool=solo`
3. 先起 Docker，再跑 API/Worker；前端：`cd frontend && npm run dev`

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

### 前端异常

```powershell
cd frontend
Remove-Item -Recurse -Force node_modules
npm install
```

---

## API 列表

| 接口 | 说明 |
|------|------|
| `GET /health` | 健康检查 |
| `POST /jd/parse` | JD 解析 |
| `POST /resume/match` | 简历匹配 |
| `GET /resume/match/history` | 匹配历史（`user_email`） |
| `GET /user/history` | 匹配 + 面试 + 计划汇总（`user_email`） |
| `POST /interview/session` | 创建面试 |
| `GET /interview/{id}/report` | 面试报告 |
| `POST /plan/generate` | 生成计划 |
| `GET /plan/latest` | 最新计划 |
| `GET /llm/stats` | LLM 统计 |

完整文档：http://127.0.0.1:8000/docs

---

## 许可证

MIT License
