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

