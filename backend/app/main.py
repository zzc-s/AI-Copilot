import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import rate_limit_dependency
from app.db.base import Base
from app.db.schema_upgrade import upgrade_schema_after_create

from app.db.session import engine
from app.models import entities  # noqa: F401

setup_logging()
app = FastAPI(title=settings.app_name)
logger = logging.getLogger(__name__)


def _frontend_dist_dir() -> Path | None:
    """与 `backend/app/main.py` 同级的 monorepo：`../frontend/dist`。"""
    repo_root = Path(__file__).resolve().parent.parent.parent
    dist = repo_root / "frontend" / "dist"
    if dist.is_dir() and (dist / "index.html").is_file():
        return dist
    return None

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

_frontend = _frontend_dist_dir()
if _frontend is not None:
    logger.info("已挂载前端构建目录（单端口访问）: %s", _frontend)
    app.mount("/", StaticFiles(directory=str(_frontend), html=True), name="spa")
else:

    @app.get("/")
    def root_info() -> dict:
        return {
            "app": settings.app_name,
            "docs": "/docs",
            "health": "/health",
            "hint": "开发：在仓库根目录执行 npm run dev（同时起后端与 Vite），或分别 cd backend / frontend。",
            "single_port": "先 cd frontend && npm run build，再启动本服务，将自动提供前端页面（本消息消失）。",
        }
