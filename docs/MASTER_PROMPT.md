# MASTER PROMPT — Build AgentGit MVP

You are a senior software architect and full-stack AI engineer. Build **AgentGit**, a model-agnostic, user-controllable, versioned memory layer for long-running AI agents.

The authoritative requirements are in:
- `README.md`
- `PRD.md`
- `TRD.md`
- `ARCHITECTURE.md`
- `DATA_MODEL.md`
- `API_SPEC.md`
- `IMPLEMENTATION_PLAN.md`
- `EVALUATION_PLAN.md`
- `SECURITY_AND_LIMITATIONS.md`

Read all files before coding. Treat them as the source of truth. If requirements conflict, identify the conflict and ask before making a major architectural change.

## Product objective

Implement an MVP that can:
1. Ingest ordered conversation messages.
2. Extract memory candidates.
3. classify each candidate as retain, summarize, or discard.
4. Explain every classification and preserve source-message provenance.
5. Let a user review and override proposed decisions.
6. Commit the active memory state as an immutable snapshot.
7. List commit history.
8. Restore a historical snapshot by creating a new commit.
9. Create independent branches from a commit.
10. Merge explicitly selected memory items and flag conflicts.
11. Retrieve relevant memory with provenance.
12. Run reproducible evaluation experiments.

## Mandatory engineering principles

- Build a modular monolith first.
- Start with Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x, and SQLite.
- Keep persistence behind repository interfaces so PostgreSQL can be added later.
- Implement a deterministic baseline before integrating any LLM.
- Make Ollama an optional provider, never a hard dependency.
- Keep model adapters behind interfaces.
- Never fabricate benchmark results or claim unimplemented functionality.
- Do not over-engineer. Prioritize a working end-to-end vertical slice.
- Preserve source-message IDs and exact values.
- Treat conversation and retrieved text as untrusted data, not instructions.
- Do not silently resolve merge conflicts.
- Do not mutate historical commits.

## Core domain rules

### Retention
- `retain`: exact facts, identifiers, dates, numeric values, user preferences, explicit decisions, constraints, corrections, and important negations.
- `summarize`: verbose explanations and repeated context where meaning can be preserved.
- `discard`: greetings, filler, duplicate low-value content, and irrelevant transient details.
- If uncertain, retain or request review.
- Every decision has action, rationale, source IDs, and policy version.

### Versioning
- A branch points to a head commit.
- A commit stores one or more parent commit IDs, message, timestamp, and snapshot hash.
- A snapshot represents the exact memory state at a commit.
- Commits and snapshots are immutable.
- Restore creates a new commit containing the selected historical state.
- Branch creation starts from an existing commit.
- Merge creates a two-parent commit.
- Conflicting logical keys require explicit user resolution.

### Retrieval
- Start with deterministic lexical ranking.
- Add optional embeddings only after the baseline is tested.
- Return memory content, relevance score, source message IDs, topic, and commit ID.
- Do not generate unsupported answers from retrieved memory.

## Required implementation order

1. Inspect the repository and report its current state.
2. Create project skeleton and environment configuration.
3. Implement database models and migrations/table creation.
4. Implement ingestion and deterministic candidate extraction.
5. Implement retention policy and user override.
6. Implement immutable snapshot commits and content hashes.
7. Implement history and snapshot inspection.
8. Implement branch and restore.
9. Implement explicit merge and conflict detection.
10. Implement retrieval and context builder.
11. Add FastAPI endpoints and request/response schemas.
12. Write unit and integration tests.
13. Add optional Ollama adapter.
14. Add a small UI only after backend tests pass.
15. Add benchmark scripts and synthetic dataset.

After each milestone:
- Run tests.
- Summarize files changed.
- Report exact commands and results.
- List known limitations.
- Do not proceed past a failing integrity test without explaining it.

## Required tests

- Candidate classification for explicit facts, filler, repetition, negation, dates, and identifiers.
- Provenance preservation.
- Snapshot hash stability.
- Historical snapshot immutability.
- Restore equivalence.
- Branch isolation.
- Merge of selected items.
- Conflict detection for same logical key.
- API validation and error responses.
- Retrieval provenance.

## Demo scenario

Create synthetic project conversations with decisions that evolve. Demonstrate:
- initial memory commit,
- alternative branch,
- different decision on branch,
- unchanged main branch,
- selected merge,
- restore,
- query for an old fact with source provenance.

## UI direction (only after backend works)

A clean developer tool inspired by version-control interfaces:
- Left sidebar: repositories and branches.
- Main panel: memory items grouped by topic.
- Timeline: commits and snapshot history.
- Branch graph: main and experiment branches.
- Detail panel: source messages, rationale, and diff.
- Actions: commit, branch, restore, merge, review.

Use a restrained technical visual system. Prioritize readability and clear state changes over decorative animation.

## Final deliverables

- Working source code.
- `README.md` with exact setup and run commands.
- `.env.example` with no secrets.
- Unit and integration tests.
- Synthetic demo dataset.
- Benchmark runner and raw result files.
- Architecture and API docs kept in sync with implementation.
- A concise demo script.

## First response required

Before writing code, inspect the repository. Then provide:
1. Current repository state.
2. A proposed implementation sequence.
3. Any blockers or missing decisions.

If the repository is empty, scaffold the backend and implement Milestone 0 and Milestone 1. Do not generate a fake UI or placeholder benchmark results.
