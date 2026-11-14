# NerfSQL

**Schema-aware, self-correcting Text-to-SQL pipeline using LangGraph + Groq**

---

## Overview

NerfSQL is a schema-aware text-to-SQL system that converts natural language queries into executable SQL, validates them against a live database, and iteratively corrects errors until a valid result is produced.

The system uses:

- Retrieval-Augmented Generation (RAG) over database schema
- A constrained LLM loop for SQL generation and correction
- Execution-based validation against a real database
- Stateful orchestration via LangGraph
- Fast inference using Groq models

---

## Key Features

### TOON-Based LLM I/O

- LLM-facing schema context is serialized in **TOON** (Token-Oriented Object Notation)
- SQL generation and correction prompts require TOON responses with a `sql` field
- Internal parser extracts SQL deterministically from TOON output

### 1. Schema-Aware Retrieval

- Embeds database schema (tables, columns, relationships)
- Retrieves only relevant schema chunks per query
- Avoids context overflow and irrelevant joins

---

### 2. Controlled SQL Generation

- Generates SQL using filtered schema context
- Supports multiple dialects (PostgreSQL, MySQL, etc.)
- Enforces read-only constraints (no `DROP`, `DELETE`, etc.)

---

### 3. Execution-Based Validation

- Runs generated SQL on a live database
- Captures:
  - syntax errors
  - missing columns/tables
  - invalid joins

---

### 4. Self-Correcting Loop (Bounded)

- Parses DB errors and feeds them back to the LLM
- Iteratively refines queries
- Stops after a configurable retry limit

---

### 5. Deterministic Guardrails

- Query sanitizer blocks destructive operations
- Schema validator checks table/column existence pre-execution
- Retry budget prevents infinite loops

---

### 6. Observability

- Full execution trace via LangGraph state
- Logs:
  - retrieved schema
  - generated SQL per iteration
  - errors and corrections

---

## Architecture

```
User Query
   │
   ▼
Schema Retriever (Vector DB)
   │
   ▼
SQL Generator (LLM)
   │
   ▼
Pre-Execution Validator
   │
   ▼
SQL Execution (DB)
   │
   ├── Success ───────────────► Return Result
   │
   ▼
Error Parser
   │
   ▼
Correction Loop (LLM)
   │
   └── Retry (bounded)
```

---

## Tech Stack

- **Orchestration:** LangGraph
- **LLM Inference:** Groq
- **Embeddings:** SentenceTransformers / OpenAI-compatible
- **Vector Store:** Pinecone (primary) + FAISS fallback
- **Database:** PostgreSQL / MySQL / SQLite
- **Backend:** Python (FastAPI optional)

---

## Project Structure

```
NerfSQL/
│
├── app/
│   ├── graph/              # LangGraph nodes and edges
│   ├── retriever/          # Schema embedding + retrieval
│   ├── llm/                # Groq client + prompts
│   ├── db/                 # DB connection + execution
│   ├── validators/         # SQL + schema validation
│   ├── utils/              # logging, parsing, helpers
│
├── configs/
│   ├── model.yaml
│   ├── db.yaml
│
├── data/
│   ├── schema_chunks.json
│
├── tests/
│   ├── eval_queries.json   # input + expected outputs
│
├── scripts/
│   ├── ingest_schema.py
│
├── README.md
└── requirements.txt
```

---

## Installation

```bash
git clone https://github.com/sdm0p/NerfSQL.git
cd NerfSQL

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

---

