# Architecture

The MVP uses a single-agent orchestration model:

1. Frontend uploads and displays paper artifacts.
2. Backend runs ingestion and overview generation.
3. Chat requests go through a paper companion agent.
4. Agent reads memory, selects retrieval strategy, and generates grounded answers.

Initial implementation uses in-memory mock repositories while preserving module boundaries for PostgreSQL, Redis, and Qdrant.
