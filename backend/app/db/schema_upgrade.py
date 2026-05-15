"""对已有 PostgreSQL 库补列（create_all 不会 alter 旧表）。"""
from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.core.config import settings


def upgrade_schema_after_create(engine: Engine) -> None:
    dim = settings.embedding_dim
    insp = inspect(engine)
    if not insp.has_table("job_descriptions"):
        return

    def colnames(table: str) -> set[str]:
        return {c["name"] for c in insp.get_columns(table)}

    emb_sql = f"vector({dim})" if settings.pgvector_enabled else "JSONB"

    with engine.begin() as conn:
        if "embedding" not in colnames("resumes"):
            conn.execute(text(f"ALTER TABLE resumes ADD COLUMN embedding {emb_sql};"))
        if "embedding" not in colnames("job_descriptions"):
            conn.execute(text(f"ALTER TABLE job_descriptions ADD COLUMN embedding {emb_sql};"))
        if insp.has_table("jd_segments") and "embedding" not in colnames("jd_segments"):
            conn.execute(text(f"ALTER TABLE jd_segments ADD COLUMN embedding {emb_sql};"))
        if insp.has_table("llm_logs") and "model_name" not in colnames("llm_logs"):
            conn.execute(text("ALTER TABLE llm_logs ADD COLUMN model_name VARCHAR(128);"))
