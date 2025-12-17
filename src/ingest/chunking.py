import re
from dataclasses import dataclass

@dataclass
class SectionChunk:
    section: str
    text: str

def split_sections(text: str) -> list[tuple[str, str]]:
    # Simple markdown-ish heading split
    lines = text.splitlines()
    sections = []
    current_title = "ROOT"
    buf = []

    for line in lines:
        if re.match(r"^\s*#{1,6}\s+", line):
            if buf:
                sections.append((current_title, "\n".join(buf).strip()))
                buf = []
            current_title = re.sub(r"^\s*#{1,6}\s+", "", line).strip()[:180] or "UNTITLED"
        else:
            buf.append(line)

    if buf:
        sections.append((current_title, "\n".join(buf).strip()))
    return [(t, s) for (t, s) in sections if s]

def chunk_text(text: str, chunk_chars: int = 1200, overlap: int = 150) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= chunk_chars:
        return [text]
    chunks = []
    i = 0
    while i < len(text):
        j = min(len(text), i + chunk_chars)
        chunks.append(text[i:j].strip())
        if j == len(text):
            break
        i = max(0, j - overlap)
    return [c for c in chunks if c]

def build_chunks(raw_text: str) -> list[SectionChunk]:
    out: list[SectionChunk] = []
    for title, sec_text in split_sections(raw_text):
        for c in chunk_text(sec_text):
            out.append(SectionChunk(section=title, text=c))
    return out
