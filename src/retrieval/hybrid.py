from src.retrieval.retrieve import dense_retrieve, RetrievedChunk
from src.retrieval.lexical import lexical_retrieve

def hybrid_retrieve(question: str, dense_k: int = 6, lexical_k: int = 6, final_k: int = 10) -> list[RetrievedChunk]:
    dense = dense_retrieve(question, top_k=dense_k)
    lex = lexical_retrieve(question, top_k=lexical_k)

    by_id: dict[int, RetrievedChunk] = {}
    for c in dense + lex:
        by_id[c.chunk_id] = c

    # sort: prefer higher score; note scores come from different systems so keep simple
    merged = list(by_id.values())
    merged.sort(key=lambda x: x.score, reverse=True)

    return merged[:final_k]
