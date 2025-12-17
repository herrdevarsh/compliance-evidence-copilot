from dataclasses import asdict
import re
from src.retrieval.retrieve import RetrievedChunk

CITE_RE = re.compile(r"\[(?P<doc>[^@\]]+)@(?P<ver>[^#\]]+)#(?P<chunk>\d+)\]")

def extract_citations(answer: str) -> list[dict]:
    cites = []
    for m in CITE_RE.finditer(answer):
        cites.append(
            {
                "doc_id": m.group("doc"),
                "version": m.group("ver"),
                "chunk_id": int(m.group("chunk")),
                "raw": m.group(0),
            }
        )
    # de-dupe
    uniq = {(c["doc_id"], c["version"], c["chunk_id"]): c for c in cites}
    return list(uniq.values())

def build_evidence_pack(question: str, answer: str, chunks: list[RetrievedChunk]) -> dict:
    citations = extract_citations(answer)

    # attach excerpts for cited chunks
    chunk_map = {(c.doc_id, c.version, c.chunk_id): c for c in chunks}
    cited_excerpts = []
    missing = 0
    for c in citations:
        key = (c["doc_id"], c["version"], c["chunk_id"])
        if key in chunk_map:
            rc = chunk_map[key]
            cited_excerpts.append(
                {
                    **c,
                    "section": rc.section,
                    "excerpt": rc.text[:600],
                }
            )
        else:
            missing += 1

    flags = []
    if not citations:
        flags.append("NO_CITATIONS")
    if missing:
        flags.append("MISSING_CITED_CHUNKS")

    return {
        "question": question,
        "answer": answer.strip(),
        "citations": cited_excerpts,
        "flags": flags,
    }
