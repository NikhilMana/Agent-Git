# AgentGit — MVP Documentation

**Project:** AgentGit  
**Problem statement:** L&T TECHgium #52 — Efficient and User-Controllable Context Memory for Long-Running Agentic AI  
**Stage:** MVP / proof of concept  
**Status:** Pre-implementation baseline  
**Team:** Nikhil Mana, K C Roopa Shetty, Prakruthi D, Onaiza Khan

## 1. Product summary

AgentGit is a model-agnostic memory management layer for long-running AI agents. It decides what conversational information should be retained verbatim, compressed into summaries, or discarded; records every memory change as an inspectable version; and lets users inspect history, restore earlier states, branch an experiment, and merge selected changes.

The MVP focuses on proving the core workflow rather than building a production-grade agent platform.

## 2. MVP goals

1. Ingest a conversation as ordered messages.
2. classify candidate information into `retain`, `summarize`, or `discard`.
3. Persist memory items and their provenance.
4. Create immutable memory snapshots.
5. List history and restore a prior snapshot.
6. Create branches from a snapshot and merge selected memory items.
7. Retrieve relevant memories for a query.
8. Run repeatable benchmarks against a full-context and/or simple-summary baseline.

## 3. Non-goals for the MVP

- Training or fine-tuning an LLM.
- Fully autonomous multi-agent orchestration.
- Guaranteed semantic conflict resolution.
- Production multi-tenant security or enterprise SSO.
- Supporting every model provider.
- Claiming a specific token saving or accuracy improvement before experiments.

## 4. Proposed stack

- Backend: Python 3.11+ and FastAPI
- Persistence: SQLite for the first local MVP; PostgreSQL + pgvector as a later deployment option
- ORM: SQLAlchemy 2.x
- Validation: Pydantic
- Local model adapter: Ollama HTTP API, optional
- Deterministic fallback: rules-based classifier and extractive summarizer
- Embeddings: optional sentence-transformers adapter; lexical retrieval fallback
- Frontend: React + TypeScript (optional for first milestone; API/CLI demo is acceptable)
- Tests: pytest

Start with SQLite so the versioning logic can be tested without infrastructure setup. Keep repository interfaces database-agnostic.

## 5. Main user journey

1. User submits a conversation.
2. AgentGit extracts candidate facts / decisions / preferences.
3. Memory policy assigns a retention action and rationale.
4. The user reviews or edits the proposed memory changes.
5. AgentGit commits a new snapshot.
6. User can inspect history, branch from an earlier snapshot, restore it, or merge selected items.
7. A query retrieves relevant memory items with provenance.

## 6. Definition of done

The MVP is demonstrable when:
- A sample conversation creates memory items with source-message references.
- Each memory action has a reason and policy metadata.
- A commit creates a new immutable snapshot.
- History shows parent-child relationships and branch names.
- Restore creates a new commit whose content matches the selected historical snapshot (do not mutate old commits).
- Branching creates an independent line of commits.
- Merge combines explicitly selected items and records both parent commits.
- Retrieval returns relevant items and their provenance.
- Tests verify snapshot immutability, restore, branch, merge, and provenance.
- Benchmark output is reproducible and labels measured results separately from targets.

## 7. Suggested repository layout

```text
agentgit/
├── README.md
├── docs/
│   ├── PRD.md
│   ├── TRD.md
│   ├── ARCHITECTURE.md
│   ├── DATA_MODEL.md
│   ├── API_SPEC.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── EVALUATION_PLAN.md
│   ├── SECURITY_AND_LIMITATIONS.md
│   └── MASTER_PROMPT.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   └── tests/
├── frontend/                 # optional for initial MVP
├── sample_data/
└── experiments/
```

## 8. Important integrity rule

Do not present planned features as implemented. Do not invent benchmark results. Every result shown in the PPT or demo must be reproducible from a saved experiment run.
