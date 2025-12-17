import hashlib
from pathlib import Path

from sqlalchemy import select, text
from rich import print

from src.db import get_session
from src.models import Document, Chunk
from src.embeddings import embed_texts
from src.ingest.chunking import build_chunks

ALLOWED = {".md", ".txt"}


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def upsert_document(session, doc_id: str, version: str, source_path: str) -> Document:
    q = select(Document).where(Document.doc_id == doc_id, Document.version == version)
    doc = session.execute(q).scalar_one_or_none()
    if doc:
        doc.source_path = source_path
        return doc

    doc = Document(doc_id=doc_id, version=version, source_path=source_path)
    session.add(doc)
    session.flush()  # ensures doc.id is available
    return doc


def ingest_file(path: Path, doc_id: str, version: str):
    raw = path.read_text(encoding="utf-8", errors="ignore")
    chunks = build_chunks(raw)

    if not chunks:
        print(f"⚠️ Skipping {path.name}: no chunks produced")
        return

    texts = [c.text for c in chunks]
    vecs = embed_texts(texts)

    with get_session() as session:
        doc = upsert_document(session, doc_id=doc_id, version=version, source_path=str(path))

        # Remove existing chunks for this doc version (simple + safe)
        session.query(Chunk).filter(Chunk.document_id == doc.id).delete()

        # Insert new chunks
        for c, v in zip(chunks, vecs, strict=True):
            session.add(
                Chunk(
                    document_id=doc.id,
                    section=c.section,
                    text=c.text,
                    text_hash=sha256(c.text),
                    embedding=v,
                )
            )

        # IMPORTANT: Flush so the rows exist, then update tsvector for lexical retrieval
        session.flush()
        session.execute(
            text(
                "UPDATE chunks "
                "SET text_tsv = to_tsvector('english', coalesce(text,'')) "
                "WHERE document_id = :docid"
            ),
            {"docid": doc.id},
        )

        session.commit()

    print(f"✅ Ingested {path.name} as {doc_id}@{version} ({len(chunks)} chunks)")


def main():
    corpus = Path("data/corpus")
    if not corpus.exists():
        raise SystemExit("Missing data/corpus")

    # Convention: filename like policy_refunds__v2.md -> doc_id=policy_refunds, version=v2
    files = [p for p in corpus.rglob("*") if p.is_file() and p.suffix.lower() in ALLOWED]
    if not files:
        raise SystemExit("No .md/.txt files found in data/corpus")

    for p in files:
        stem = p.stem
        if "__" in stem:
            doc_id, version = stem.split("__", 1)
        else:
            doc_id, version = stem, "v1"

        ingest_file(p, doc_id=doc_id, version=version)


if __name__ == "__main__":
    main()
