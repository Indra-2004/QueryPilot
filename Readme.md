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

