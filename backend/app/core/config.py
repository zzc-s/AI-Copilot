import logging

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_log = logging.getLogger(__name__)


def _try_create_pgvector_extension(database_url: str) -> bool:
    """尝试执行 CREATE EXTENSION vector；库无 pgvector 时返回 False。连接失败会向外抛出。"""
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import NotSupportedError

    eng = create_engine(database_url, pool_pre_ping=True)
    try:
        with eng.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        return True
    except NotSupportedError:
        return False
    finally:
        eng.dispose()


class Settings(BaseSettings):
    app_name: str = "Job AI Copilot API"
    app_env: str = "dev"
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/job_copilot"
    pgvector_enabled: bool = Field(
        default=True,
        description="为 False 时不创建 vector 扩展，embedding 用 JSONB（兼容无 pgvector 的官方 Postgres）",
    )
    log_level: str = "INFO"
    cache_ttl_seconds: int = 3600

    # LLM（mock | openai | compatible）
    llm_provider: str = "mock"
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model_primary: str = "gpt-4o-mini"
    llm_model_fallback: str = ""
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 2
    llm_augment: bool = Field(
        default=True,
        description="为 True 且已配置非 mock 的 LLM 与 API Key 时，用模型增强解析/建议/题/计划等规则结果",
    )

    # Embedding（mock | openai | compatible）
    embedding_provider: str = "mock"
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536

    # ASR（mock | aliyun | openai_whisper | compatible）
    asr_provider: str = "mock"
    asr_model: str = "whisper-1"
    asr_api_key: str = ""  # 格式: "access_key_id:access_key_secret" (aliyun) 或普通 api key
    asr_app_key: str = ""  # 仅用于阿里云 ASR
    # Celery/IDE 子进程可能读不到 PATH 中的 ffmpeg；可填 ffmpeg.exe 绝对路径（环境变量 FFMPEG_PATH）
    ffmpeg_path: str = ""

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


_raw_settings = Settings()
if _raw_settings.pgvector_enabled:
    if not _try_create_pgvector_extension(_raw_settings.database_url):
        _log.warning(
            "当前 PostgreSQL 无法使用 pgvector（vector 扩展不可用），已自动改用 JSONB 存储 embedding。"
            " 需要原生向量列请使用 pgvector 镜像（如 docker compose 中的 postgres）并保证 DATABASE_URL 指向该实例。"
        )
        settings = _raw_settings.model_copy(update={"pgvector_enabled": False})
    else:
        settings = _raw_settings
else:
    settings = _raw_settings
