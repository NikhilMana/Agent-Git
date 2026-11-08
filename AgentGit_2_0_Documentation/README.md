# AgentGit 2.0 — Universal Agent Memory & Intelligent Context Layer

**Competition:** L&T TECHgium 10th Edition  
**Problem statement:** #52 — Efficient and User-Controllable Context Memory for Long-Running Agentic AI  
**Team:** Nikhil Mana, K C Roopa Shetty, Prakruthi D, Onaiza Khan  
**Status:** Existing MVP reported by the team; integration and context-orchestration upgrade proposed.

## 1. Product direction

AgentGit is evolving from a conversation-memory and version-control MVP into a model-agnostic memory and task-aware context layer for existing AI agent environments.

AgentGit should help compatible agents:
- Preserve important conversation facts, decisions, constraints and progress.
- Retrieve only task-relevant memory instead of replaying entire conversation histories.
- Discover relevant codebase files, symbols and dependencies without blindly indexing the whole repository into every prompt.
- Version memory using immutable snapshots, history, branches, merges and restore.
- Exchange context and memory operations through MCP.
- Capture important task outcomes through explicit agent calls or supported host-specific lifecycle adapters.

**Core principle:** AgentGit supplies context; the host agent remains responsible for reasoning and execution. Retrieved memory is guidance, not a replacement for current source code.

## 2. Existing MVP capabilities (reported)

The supplied project README describes these capabilities/goals: conversation ingestion, retain/summarize/discard classification, provenance, immutable snapshots, history, restore, branches, selected-item merge, retrieval, and repeatable benchmarks. The team reports that an MVP and benchmark run now exist. The uploaded README itself is still labelled “Pre-implementation baseline”; reconcile its status and feature checklist with the actual repository before claiming individual features are implemented.

## 3. AgentGit 2.0 additions

1. MCP server exposing memory and context tools.
2. Antigravity integration through a lightweight project rule and MCP configuration.
3. Task-aware context orchestration.
4. Codebase intelligence index: file metadata, symbols, imports/dependencies, Git change metadata and optional embeddings.
5. Context budgeting and relevance ranking.
6. Write-back of task outcomes, decisions and changed-file summaries.
7. Host adapters for additional environments only after validating their supported interfaces.

## 4. Explicit limitations

- MCP does not automatically grant access to a host's private conversation transcript.
- MCP does not delete tokens already loaded into a model's current context window.
- Antigravity rules can instruct the agent to call AgentGit, but rules alone cannot guarantee that every host event is captured.
- Automatic capture requires a supported host lifecycle hook, extension/API, session export, or an explicit agent tool call.
- AgentGit cannot promise fewer tokens or unchanged/improved accuracy without controlled experiments.
- The codebase index can become stale; live source files and tests are authoritative.

## 5. Recommended stack

Preserve the existing stack where it works. Proposed additions:
- MCP: official Python MCP SDK, using stdio for local IDE integration initially.
- Backend: existing FastAPI/core services; MCP server calls the same application services.
- Storage: existing SQLite/PostgreSQL repository; avoid a second source of truth.
- Code parsing: Tree-sitter or language-specific parsers where useful.
- Retrieval: lexical/symbol search first; embeddings as an optional layer.
- Git metadata: read-only Git integration.
- Frontend: existing UI, if present; no redesign required for the integration milestone.

## 6. Development principle

Do not rewrite the existing MVP. First inspect the actual repository, tests, database schema, APIs and benchmark implementation. Build adapters around existing services. If an existing capability is absent or incomplete, report it and implement it with tests.

## 7. Definition of done for 2.0 integration

- MCP server starts locally using stdio.
- MCP tools call existing AgentGit services, not duplicated business logic.
- Antigravity can discover and call `agentgit_get_task_context`.
- The returned context includes provenance, freshness and token estimate.
- Codebase indexing is incremental and can be refreshed.
- Task context is bounded by a configurable token budget.
- Agent can request additional context when initial context is insufficient.
- A task outcome can be written back with changed files, decisions and tests.
- Stale or missing context triggers source inspection rather than unsupported assumptions.
- Benchmark compares normal workflow, rules-only workflow and rules + AgentGit.
- All results are measured and reproducible.
