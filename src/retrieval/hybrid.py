from src.retrieval.retrieve import dense_retrieve, RetrievedChunk
from src.retrieval.lexical import lexical_retrieve
from src.retrieval.versioning import keep_latest_per_doc

def hybrid_retrieve(question: str, dense_k: int = 6, lexical_k: int = 6, final_k: int = 10) -> list[RetrievedChunk]:
    dense = dense_retrieve(question, top_k=dense_k)
    lex = lexical_retrieve(question, top_k=lexical_k)

    by_id: dict[int, RetrievedChunk] = {}
    for c in dense + lex:
        by_id[c.chunk_id] = c

    merged = list(by_id.values())

    # Prefer latest version per doc_id (kills v1 vs v2 confusion)
    merged = keep_latest_per_doc(merged)

    merged.sort(key=lambda x: x.score, reverse=True)
    return merged[:final_k]
