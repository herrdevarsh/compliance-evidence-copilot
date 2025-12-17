from sentence_transformers import SentenceTransformer
from src.config import settings

_model = None

def get_embedder() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embed_model)
    return _model

def embed_texts(texts: list[str]) -> list[list[float]]:
    m = get_embedder()
    vecs = m.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
    return [v.tolist() for v in vecs]
