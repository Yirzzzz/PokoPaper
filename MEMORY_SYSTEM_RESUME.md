# Memory System Work Summary

## Project Scope

Designed and implemented a layered memory system for a local single-user paper companion product, with clear separation between:

- conversation-scoped instant memory
- conversation-scoped session summary memory
- user-scoped entity memory
- paper-scoped entity memory

The goal was to improve conversation continuity and memory visibility without reintroducing complex long-term retrieval or unstable routing logic.

## What Was Implemented

### 1. Conversation Model Refactor

Introduced an explicit conversation model to separate:

- `global_chat` conversations on the main chat page
- `paper_chat` conversations bound 1:1 to each paper

Implemented:

- stable `conversation_id`
- isolated message history per conversation
- multiple global conversations with create / switch / delete
- fixed single paper conversation per paper

This removed history leakage between the main chat view and paper-specific chats.

### 2. Instant Memory Window

Built a conversation-scoped instant memory layer that keeps only the most recent QA window in active prompt context.

Implemented:

- sliding-window instant memory
- current window limited to recent conversation turns
- automatic eviction of older turns from the active window
- direct prompt injection of recent raw messages

This supports follow-up questions like:

- "What did I just ask?"
- "What were we discussing just now?"

without requiring long-term retrieval.

### 3. Session Summary Memory

Added a second short-term layer for compressed session history outside the active window.

Implemented:

- `SessionSummaryMemory` structure
- incremental summary updates
- threshold-triggered summarization instead of summarizing every turn
- summary fields including:
  - `summary_text`
  - `discussion_topics`
  - `key_points`
  - `open_questions`
  - `covered_message_until`

Behavior:

- recent messages remain the primary context
- older out-of-window messages are compressed into summary memory
- low-signal turns such as greetings and acknowledgements are filtered out

### 4. User Entity Memory

Restored a minimal user-level memory under `user:local-user` for long-lived background information shared across conversations.

Implemented separated update paths:

- upload / parsing driven updates:
  - `read_paper_ids`
  - `recent_topics`
  - `paper_link_candidates`
- conversation driven updates:
  - `weak_concepts`
  - `mastered_concepts`
  - `preferred_explanation_style`
  - `cross_paper_links`

This kept reading history and understanding state as separate signals instead of mixing them in a single update path.

### 5. Paper Entity Memory

Added structured memory cards for each paper, generated during ingestion from the paper overview.

Implemented fields such as:

- motivation
- problem
- core proposal
- method
- value
- resolved gap
- test data / evidence
- key results
- summary card

This provided a compact, reusable representation of each paper for later recall and inspection.

### 6. Prompt Integration

Integrated memory into prompts as plain supporting context, without intent-classification instructions.

Prompt now uses separate blocks for:

- recent conversation context
- earlier session summary
- user background memory

Not implemented:

- explicit question-type routing inside the prompt
- "memory sufficiency" refusal logic
- cross-paper retrieval orchestration

### 7. Memory Visualization

Added dedicated UI pages for memory inspection:

- instant memory page
- session summary page
- user entity memory page
- paper entity memory page

These pages expose stored memory by conversation or scope and make debugging easier without relying on logs alone.

### 8. Ingestion Improvements Related to Memory

Improved PDF title extraction for paper ingestion by:

- switching from single-line title detection to title-block detection
- merging multi-line titles
- stopping before author blocks
- filtering preprint / arXiv / affiliation noise

This improved paper metadata quality, which also helped downstream paper memory generation.

## Engineering Characteristics

The implementation focused on pragmatic stability rather than a full research-grade memory architecture.

Key engineering decisions:

- keep memory scopes explicit
- isolate raw history by conversation
- avoid overloading prompts with routing instructions
- make memory inspectable in the UI
- provide heuristic fallback when LLM-based summarization is unavailable

## Testing Coverage Added

Added and updated tests for:

- conversation isolation
- multiple global conversations
- fixed paper conversation binding
- instant memory window behavior
- session summary triggering and isolation
- user entity memory updates
- paper entity memory generation
- prompt memory block injection
- PDF title extraction edge cases

## Boundaries

This work did not implement or restore:

- embedding-based memory retrieval
- global reading recall
- cross-paper semantic retrieval engine
- full Memory Lab workflow
- complex autonomous memory routing

The system currently focuses on stable short-term continuity, structured memory storage, and inspectable memory behavior.
