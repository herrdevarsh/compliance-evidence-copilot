from sqlalchemy import text
from src.db import get_session
from src.retrieval.retrieve import RetrievedChunk

def lexical_retrieve(question: str, top_k: int = 6) -> list[RetrievedChunk]:
    sql = text("""
        SELECT c.id as chunk_id, d.doc_id, d.version, c.section, c.text,
               ts_rank_cd(c.text_tsv, plainto_tsquery('english', :q)) AS score
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE c.text_tsv @@ plainto_tsquery('english', :q)
        ORDER BY score DESC
        LIMIT :k
    """)
    with get_session() as session:
        rows = session.execute(sql, {"q": question, "k": top_k}).mappings().all()

    return [
        RetrievedChunk(
            chunk_id=r["chunk_id"],
            doc_id=r["doc_id"],
            version=r["version"],
            section=r["section"],
            text=r["text"],
            score=float(r["score"] or 0.0),
        )
        for r in rows
    ]
