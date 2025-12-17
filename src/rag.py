from src.config import settings
from src.retrieval.hybrid import hybrid_retrieve
from src.generation.prompting import build_prompt
from src.generation.llm import generate_text
from src.evidence_pack.pack import build_evidence_pack, extract_citations

REFUSAL_TEXT = (
    "I don't have enough information in the provided sources to answer this confidently. "
    "Please provide the relevant policy/document section."
)

def ask(question: str) -> dict:
    chunks = hybrid_retrieve(question, dense_k=settings.top_k, lexical_k=settings.top_k)

    if not chunks:
        return {
            "question": question,
            "answer": REFUSAL_TEXT,
            "citations": [],
            "flags": ["NO_RETRIEVAL"],
        }

    # First attempt
    system, user = build_prompt(question, chunks, strict=False)
    answer = generate_text(system, user)

    # Guardrail: if no citations, retry strictly once
    if not extract_citations(answer):
        system2, user2 = build_prompt(question, chunks, strict=True)
        answer2 = generate_text(system2, user2)
        answer = answer2

    # Final enforcement: still no citations => refuse
    if not extract_citations(answer):
        answer = REFUSAL_TEXT

    return build_evidence_pack(question, answer, chunks)
