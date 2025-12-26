# Compliance Evidence Copilot
**Audit-first RAG for policy/compliance Q&A: answer with evidence or refuse.**

Most RAG demos optimize for “nice answers”. This repo optimizes for **risk control**:

- If evidence exists → answer **briefly** with **citations**
- If evidence is missing/uncertain → **refuse** (don’t guess)
- If documents have multiple versions → prefer **latest** by default

The core deliverable is an **Evidence Pack** (answer + citations + excerpts), suitable for audit-style workflows.

---

## Why this matters (real problem)

Compliance/legal/security teams waste time:
- searching policies and SOPs
- answering repeat questions
- preparing audit evidence

The costly failure mode is a model that sounds confident but is wrong. This project focuses on **groundedness, versioning, and safety**.

---

## Guarantees (what the system enforces)

✅ Citations in the format: `[doc_id@version#chunk_id]`  
✅ Evidence Pack includes cited excerpts  
✅ If no citations can be produced → refuse  
✅ Latest versions preferred unless user explicitly asks for older version

**Non-goals**
- No agent tool-calling
- No fancy UI (yet)
- No “trust me bro” results: evaluation is required

---

## System Architecture (ASCII)

### High-level data + control flow

```
                         ┌───────────────────────────────┐
                         │        data/corpus/*.md        │
                         │  doc_id__vN.md (versioned)     │
                         └───────────────┬───────────────┘
                                         │ ingest
                                         v
┌───────────────────────────────────────────────────────────────────────────────┐
│                                   DATABASE                                    │
│                            Postgres + pgvector + FTS                           │
│                                                                               │
│   documents(doc_id, version, source_path, ...)                                 │
│   chunks(id, document_id, section, text, embedding, text_tsv, ...)             │
└───────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         │ query
                                         v
┌──────────────────────┐     ┌──────────────────────┐
│ Dense Retrieval       │     │ Lexical Retrieval     │
│ pgvector cosine NN    │     │ Postgres tsvector FTS │
└───────────┬──────────┘     └───────────┬──────────┘
            │ merge (union by chunk_id)   │
            └───────────────┬─────────────┘
                            v
                 ┌─────────────────────────┐
                 │ Version Filter           │
                 │ keep latest per doc_id   │
                 │ (unless user asks v1)    │
                 └─────────────┬───────────┘
                               v
                   ┌─────────────────────────┐
                   │ Prompt Builder           │
                   │ - sources (top-k)        │
                   │ - cite-or-refuse rules   │
                   └─────────────┬───────────┘
                               v
                    ┌────────────────────────┐
                    │ LLM (Ollama)            │
                    │ - output cap            │
                    │ - strict retry optional │
                    └─────────────┬──────────┘
                               v
                 ┌────────────────────────────┐
                 │ Evidence Pack Builder        │
                 │ - extract citations          │
                 │ - attach excerpts            │
                 │ - flags (NO_CITATIONS etc.)  │
                 └─────────────┬──────────────┘
                               v
                ┌────────────────────────────────┐
                │ API/CLI JSON Output              │
                │ {answer, citations[], flags[]}   │
                └────────────────────────────────┘
```

### Runtime request path

```
Client -> POST /ask
   |
   |--> hybrid retrieve (dense + lexical)
   |--> apply version filter (latest-by-default)
   |--> build prompt with sources + rules
   |--> LLM generate
   |--> if no citations -> retry strict -> else refuse
   |--> return Evidence Pack JSON
```

---

## Output format (Evidence Pack)

Example response shape:

```json
{
  "question": "How long do refunds take?",
  "answer": "Refunds are processed within 7 days after approval. [refund_policy@v2#15]",
  "citations": [
    {
      "doc_id": "refund_policy",
      "version": "v2",
      "chunk_id": 15,
      "section": "Refund Policy",
      "excerpt": "Refunds are processed within 7 days after approval."
    }
  ],
  "flags": []
}
```

---

## Repo structure

```
compliance-evidence-copilot/
  api/
    main.py
  data/
    corpus/                  # docs (.md/.txt) with version naming
    eval/                    # jsonl eval sets + results
  infra/
    docker-compose.yml       # postgres+pgvector (+ mlflow optional)
  src/
    ingest/
      chunking.py
      ingest.py
    retrieval/
      retrieve.py            # dense
      lexical.py             # FTS
      hybrid.py              # merge
      versioning.py          # latest-per-doc
    generation/
      prompting.py
      llm.py                 # Ollama client (caps output/context)
    evidence_pack/
      pack.py
    eval/
      run_eval.py
    config.py
    db.py
    init_db.py
    models.py
  requirements.txt
  README.md
```

---

## Document naming (versioning)

Put docs into `data/corpus/`:

- `refund_policy__v1.md`
- `refund_policy__v2.md`

Parsed as:
- `doc_id = refund_policy`
- `version = v1 / v2`

---

## Quickstart (PowerShell)

### 1) Start services
```powershell
docker compose -f .\infra\docker-compose.yml up -d
```

### 2) Activate venv
```powershell
.\.venv\Scripts\Activate.ps1
```

### 3) Init DB + enable FTS (safe to run anytime)
```powershell
python -m src.init_db
python -m src.migrations.add_fts
```

### 4) Ingest corpus
```powershell
python -m src.ingest.ingest
```

### 5) Run CLI
```powershell
python -m src.cli "How long do refunds take?"
```

### 6) Run API
```powershell
uvicorn api.main:app --reload --port 8000
```

Test:
```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/ask `
  -ContentType "application/json" `
  -Body '{"question":"How long do refunds take?"}' | ConvertTo-Json -Depth 6
```

### 7) Run evaluation
```powershell
python -m src.eval.run_eval
```

---

## Ollama setup (recommended small model)

Large models can be slow on CPU. Pull a smaller model for faster eval:

```powershell
'{"name":"llama3.2:3b"}' | Set-Content -Encoding ascii .\pull.json
curl.exe -N -X POST "http://localhost:11434/api/pull" -H "Content-Type: application/json" --data-binary "@pull.json"
Invoke-RestMethod -Uri "http://localhost:11434/api/tags"
```

Set `.env`:
```env
OLLAMA_MODEL=llama3.2:3b
TOP_K=3
```

---

## Evaluation (the differentiator)

RAG is only useful if you measure failure modes.

**Included eval sets**
- `questions.jsonl` : answerable/unanswerable
- `attack_set.jsonl` : prompt injection attempts
- `version_set.jsonl` : latest vs explicit v1
- `contradiction_set.jsonl` : (optional) conflict handling

**Metrics (current)**
- `no_citation_non_refusal_rate` (bad: answered without citations)
- `refusal_rate`
- `injection_success_rate` (bad: uncited answer under attack)

**Planned**
- claim-level groundedness (supported vs unsupported sentences)
- version attribution accuracy
- citation precision/recall (do cited excerpts support the claim?)

---

## Roadmap

1) Claim-level groundedness scoring  
2) Larger injection test suite + scoring  
3) MLflow ablations (top_k, truncation, hybrid on/off)  
4) Cross-encoder reranker to improve citation correctness  
5) Clear contradiction policy: latest wins unless user requests older

---
