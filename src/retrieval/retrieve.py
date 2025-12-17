from dataclasses import dataclass
from sqlalchemy import select
from src.db import get_session
from src.models import Chunk, Document
from src.embeddings import embed_texts

@dataclass
class RetrievedChunk:
    chunk_id: int
    doc_id: str
    version: str
    section: str
    text: str
    score: float  # higher is better

def dense_retrieve(question: str, top_k: int = 6) -> list[RetrievedChunk]:
    qvec = embed_texts([question])[0]

    dist_expr = Chunk.embedding.cosine_distance(qvec).label("dist")

    stmt = (
        select(Chunk, Document, dist_expr)
        .join(Document, Document.id == Chunk.document_id)
        .order_by(dist_expr.asc())
        .limit(top_k)
    )

    with get_session() as session:
        rows = session.execute(stmt).all()

    out: list[RetrievedChunk] = []
    for chunk, doc, dist in rows:
        dist = float(dist)
        score = 1.0 - dist  # normalized-ish similarity
        out.append(
            RetrievedChunk(
                chunk_id=chunk.id,
                doc_id=doc.doc_id,
                version=doc.version,
                section=chunk.section,
                text=chunk.text,
                score=score,
            )
        )
    return out
