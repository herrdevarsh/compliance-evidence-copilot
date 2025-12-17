import re
from collections import defaultdict
from src.retrieval.retrieve import RetrievedChunk

def _version_key(v: str) -> tuple:
    # supports v1, v2, v10 etc. Unknown versions go last.
    m = re.match(r"^v(\d+)$", (v or "").strip().lower())
    if m:
        return (0, int(m.group(1)))
    return (1, v)

def keep_latest_per_doc(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    by_doc = defaultdict(list)
    for c in chunks:
        by_doc[c.doc_id].append(c)

    filtered: list[RetrievedChunk] = []
    for doc_id, items in by_doc.items():
        latest_ver = sorted({c.version for c in items}, key=_version_key)[-1]
        filtered.extend([c for c in items if c.version == latest_ver])

    return filtered
