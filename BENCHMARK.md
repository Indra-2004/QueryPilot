# NerfSQL reproducible metrics

The benchmark contains 55 labeled scenarios: 20 single-table questions, 30 join or aggregation questions, and 5 deliberately unanswerable questions. It compares connection-scoped Pinecone retrieval (`rag`) with the complete selected database schema (`full`).

## What is measured

- Semantic accuracy: required tables and expected result values are present.
- Hallucination rate: generated SQL references an unavailable table, or an unanswerable question returns data.
- Token consumption: input tokens reported by the LLM provider across generation, semantic validation, and correction calls.
- Retry count and LLM-call count.
- End-to-end p50, p95, and p99 latency.

The files under `benchmark-results/` are generated evidence and should include the model, timestamp, connection, and configuration when results are reported publicly.

