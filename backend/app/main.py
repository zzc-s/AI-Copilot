import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from scalar_fastapi import get_scalar_api_reference

from app.api.routes import router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import rate_limit_dependency
from app.db.base import Base
from app.db.schema_upgrade import upgrade_schema_after_create

from app.db.session import engine
from app.models import entities  # noqa: F401

setup_logging()
logger = logging.getLogger(__name__)

OPENAPI_TAGS = [
    {"name": "系统", "description": "健康检查与异步任务状态"},
    {"name": "JD", "description": "职位描述解析"},
    {"name": "简历", "description": "简历与 JD 匹配"},
    {"name": "面试", "description": "模拟面试会话与作答"},
    {"name": "计划", "description": "7 天训练计划"},
    {"name": "用户", "description": "按邮箱查询历史记录"},
    {"name": "LLM", "description": "大模型调用日志与统计"},
    {"name": "管理", "description": "运维与数据回填"},
]

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "求职 AI Copilot API：JD 解析、简历匹配、模拟面试、改进计划。"
        "文档推荐访问 **/doc.html**（Knife4j），备用 **/scalar**、**/docs**。"
    ),
    openapi_tags=OPENAPI_TAGS,
    docs_url="/docs",
    redoc_url="/redoc",
)

_APP_DIR = Path(__file__).resolve().parent
_KNIFE4J_DIR = _APP_DIR / "static" / "knife4j"


def _frontend_dist_dir() -> Path | None:
    """与 `backend/app/main.py` 同级的 monorepo：`../frontend/dist`。"""
    repo_root = _APP_DIR.parent.parent
    dist = repo_root / "frontend" / "dist"
    if dist.is_dir() and (dist / "index.html").is_file():
        return dist
    return None


def _register_knife4j_routes() -> bool:
    """挂载 Knife4j 静态 UI；返回是否已成功注册。"""
    doc_html = _KNIFE4J_DIR / "doc.html"
    webjars = _KNIFE4J_DIR / "webjars"
    if not doc_html.is_file() or not webjars.is_dir():
        logger.warning(
            "Knife4j 静态资源未找到（%s），请执行 backend/scripts/fetch_knife4j_ui.ps1",
            _KNIFE4J_DIR,
        )
        return False

    @app.get("/doc.html", include_in_schema=False)
    async def knife4j_doc() -> FileResponse:
        return FileResponse(doc_html)

    @app.get("/group.json", include_in_schema=False)
    async def knife4j_group() -> FileResponse:
        return FileResponse(_KNIFE4J_DIR / "group.json")

    app.mount("/webjars", StaticFiles(directory=str(webjars)), name="knife4j-webjars")
    img_dir = _KNIFE4J_DIR / "img"
    if img_dir.is_dir():
        app.mount("/img", StaticFiles(directory=str(img_dir)), name="knife4j-img")

    @app.get("/v3/api-docs/swagger-config", include_in_schema=False)
    async def knife4j_swagger_config() -> dict:
        return {
            "configUrl": "/v3/api-docs/swagger-config",
            "urls": [
                {
                    "url": "/openapi.json",
                    "name": "Job AI Copilot",
                    "displayName": "Job AI Copilot",
                    "swaggerVersion": "3.0",
                }
            ],
        }

    @app.get("/swagger-resources", include_in_schema=False)
    async def knife4j_swagger_resources() -> list[dict]:
        return [
            {
                "name": "Job AI Copilot",
                "url": "/openapi.json",
                "swaggerVersion": "3.0",
                "location": "/openapi.json",
            }
        ]

    logger.info("Knife4j 文档已启用: /doc.html")
    return True


def _register_scalar_route() -> None:
    @app.get("/scalar", include_in_schema=False)
    async def scalar_docs():
        return get_scalar_api_reference(
            openapi_url=app.openapi_url,
            title=f"{settings.app_name} API",
        )


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    upgrade_schema_after_create(engine)


@app.middleware("http")
async def add_rate_limit(request: Request, call_next):
    await rate_limit_dependency(request)
    return await call_next(request)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(router)
_register_scalar_route()
_knife4j_ok = _register_knife4j_routes()

DOCS_HINT = {
    "knife4j": "/doc.html" if _knife4j_ok else None,
    "scalar": "/scalar",
    "swagger": "/docs",
    "redoc": "/redoc",
    "openapi": "/openapi.json",
}

_frontend = _frontend_dist_dir()
if _frontend is not None:
    logger.info("已挂载前端构建目录（单端口访问）: %s", _frontend)
    app.mount("/", StaticFiles(directory=str(_frontend), html=True), name="spa")
else:

    @app.get("/")
    def root_info() -> dict:
        return {
            "app": settings.app_name,
            "docs": DOCS_HINT,
            "health": "/health",
            "hint": "开发：在仓库根目录执行 npm run dev（同时起后端与 Vite），或分别 cd backend / frontend。",
            "single_port": "先 cd frontend && npm run build，再启动本服务，将自动提供前端页面（本消息消失）。",
            "knife4j_setup": None
            if _knife4j_ok
            else "运行 backend/scripts/fetch_knife4j_ui.ps1 后重启 API 以启用 /doc.html",
        }
