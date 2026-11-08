# AgentGit 2.0 — Implementation Roadmap

## Phase 0 — Repository audit (mandatory)
- Inspect actual project tree, README, dependencies, services, database and tests.
- Run existing tests and benchmark once.
- Identify exact current capabilities and gaps.
- Record baseline Git commit and database backup.
- Produce a compatibility map: requirement -> existing module -> change required.

**Exit:** no code changes until the audit is documented.

## Phase 1 — MCP adapter
- Add official Python MCP SDK.
- Implement local stdio server.
- Wrap existing retrieval, commit/history and restore services.
- Add `agentgit_get_task_context` initially using conversation memory only.
- Add structured errors and tests.

**Exit:** Antigravity discovers and calls task-context retrieval.

## Phase 2 — Antigravity rules and write-back
- Add workspace rule template.
- Implement `agentgit_record_task_outcome`.
- Verify cross-session retrieval.
- Keep automatic transcript capture claims out until supported host APIs are proven.

**Exit:** task starts with memory retrieval and ends with verified outcome write-back.

## Phase 3 — Codebase index
- Add repository registration and safe root validation.
- Implement file filtering, hashing and incremental refresh.
- Add symbol/import parsing for languages present in repository.
- Add freshness checks.
- Add `agentgit_get_file_context`.

**Exit:** task context returns relevant paths/symbols with freshness metadata.

## Phase 4 — Orchestrator and token budget
- Combine memory and codebase candidates.
- Rank, deduplicate and enforce budget.
- Return coverage, omissions and follow-up needs.
- Add exact-tokenizer support if available.

**Exit:** deterministic tests prove budget enforcement and source provenance.

## Phase 5 — Benchmark
- Build same-task conditions: normal, rules-only, AgentGit.
- Collect actual token telemetry where available.
- Save reproducible run artifacts.
- Analyze accuracy and token trade-offs.

**Exit:** no unsupported performance claims.

## Phase 6 — Additional hosts
- Claude Code integration.
- Cursor integration.
- Custom Python agent SDK.
- Host-specific adapters only after feature validation.

## Team work split (suggested)
- Nikhil Mana: architecture, MCP integration, context orchestrator and integration.
- K C Roopa Shetty: memory retrieval policy and classification quality.
- Prakruthi D: codebase index, persistence and API tests.
- Onaiza Khan: benchmark dataset, evaluation runs, documentation and demo validation.

Adjust roles to actual availability and skills.

## Release checklist
- Existing MVP behavior remains intact.
- Tests pass.
- MCP server works over stdio.
- Repository path restrictions tested.
- Secrets excluded from index.
- Stale index behavior tested.
- Context budget enforced.
- Provenance returned.
- Antigravity rule documented.
- Benchmark raw outputs saved.
- README accurately distinguishes implemented and planned features.
