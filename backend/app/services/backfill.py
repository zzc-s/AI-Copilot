"""开发环境用的向量回填。"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import JobDescription, JdSegment
from app.services.embedding import embed_texts, split_jd_chunks


def backfill_jd_embeddings(db: Session) -> dict[str, int]:
    updated_jd = 0
    updated_seg = 0
    jds = list(db.scalars(select(JobDescription)).all())
    for jd in jds:
        if jd.embedding is None and jd.raw_text:
            try:
                vecs, _ = embed_texts([jd.raw_text])
                if vecs:
                    jd.embedding = vecs[0]
                    updated_jd += 1
            except Exception:
                continue
        segs = list(db.scalars(select(JdSegment).where(JdSegment.jd_id == jd.id)).all())
        if not segs and jd.raw_text:
            chunks = split_jd_chunks(jd.raw_text)
            if chunks:
                try:
                    vecs, _ = embed_texts(chunks)
                    for i, txt in enumerate(chunks):
                        vec = vecs[i] if i < len(vecs) else None
                        db.add(JdSegment(jd_id=jd.id, chunk_index=i, text=txt, embedding=vec))
                        updated_seg += 1
                except Exception:
                    pass
    db.commit()
    return {"job_descriptions_embedded": updated_jd, "segments_added": updated_seg}
