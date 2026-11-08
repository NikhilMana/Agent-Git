# Technical Requirements Document — AgentGit 2.0

## 1. Preserve existing implementation

Before coding, inspect the repository and produce a capability map:
- Existing ingestion, classification, retrieval, provenance and versioning services.
- Existing API endpoints and schemas.
- Database models and migrations.
- Existing benchmark scripts and raw outputs.
- Current frontend and configuration.

Map each 2.0 requirement to an existing service or a missing component. Do not rewrite working modules.

## 2. Proposed logical modules

1. `MCPAdapter`: MCP tools/resources; translates MCP requests into application service calls.
2. `ContextOrchestrator`: task parsing, retrieval planning, ranking, deduplication and token budgeting.
3. `ConversationMemoryProvider`: wraps existing memory retrieval.
4. `CodebaseIndexer`: incremental file and symbol metadata indexing.
5. `DependencyGraph`: imports, references and related-file traversal.
6. `FreshnessManager`: content hashes, Git commit association and index invalidation.
7. `TaskWritebackService`: validates task outcome and creates memory candidates.
8. `HostIntegrationDocs`: Antigravity rules/config and later host-specific adapters.

## 3. MCP implementation

Use the official Python MCP SDK. Prefer stdio for local IDE integration. Keep the MCP process stateless where practical; use existing database and core services for state.

Tools to implement in priority order:
- `agentgit_get_task_context`
- `agentgit_search_memory`
- `agentgit_get_file_context`
- `agentgit_record_task_outcome`
- `agentgit_refresh_codebase_index`
- `agentgit_get_memory_history`
- `agentgit_commit_memory`
- `agentgit_create_branch`
- `agentgit_merge_branch`
- `agentgit_restore_snapshot`

Read-only resources may include:
- `agentgit://repositories/{repository_id}/overview`
- `agentgit://repositories/{repository_id}/branches/{branch}/memory`
- `agentgit://repositories/{repository_id}/index/status`

Do not expose write operations as read-only resources. Validate every argument and enforce repository-root authorization.

## 4. Task context request

Suggested fields:
- `task`: required string
- `repository_id`: required identifier
- `branch`: optional, default configured branch
- `current_file`: optional relative path
- `max_tokens`: optional bounded integer
- `include`: optional list: `decisions`, `constraints`, `files`, `symbols`, `dependencies`, `unfinished_tasks`, `conversation_memories`
- `changed_files`: optional list of relative paths

Response:
- `task`
- `context_sections`
- `relevant_files`: path, reason, freshness, indexed_commit, content_hash
- `symbols`: name, file, kind, signature/short description when parser supports it
- `dependencies`: source path, target path, relation
- `memory_items`: content, score, category, provenance, commit ID, freshness
- `confidence` or coverage indicator with clearly defined computation
- `estimated_tokens` and tokenizer/estimation method
- `omitted_items` / `truncation_notice`
- `follow_up_queries` or `needs_more_context`

Never fabricate a calibrated probability. If a numerical confidence score is not calibrated, call it a heuristic relevance/coverage score and document its meaning.

## 5. Codebase indexing

For each configured repository:
- Resolve and store canonical repository root.
- Reject paths outside root after normalization and symlink resolution.
- Respect `.gitignore` and configurable exclusion rules.
- Exclude `.env`, credentials, private keys, build outputs, dependency folders, binaries and large generated files by default.
- Record file path, language, size, content hash, last indexed time and Git commit.
- Extract symbols/imports with Tree-sitter or language-specific parsers when available.
- Fallback to filename/path and lexical indexing when parser unsupported.
- Build dependency edges only when evidence exists.
- Never assume a filename or symbol exists without checking the index/live file.

Index metadata and selected snippets only. The live source file remains authoritative.

## 6. Retrieval algorithm

Initial ranking should be explainable:
- Exact file path / symbol / identifier match.
- Lexical relevance.
- Memory category and explicitness.
- Dependency distance from matched files.
- Branch match.
- Recency and freshness.
- Optional embedding similarity.

Deduplicate overlapping results. Keep hard constraints and exact decisions above generic summaries. Include source references for every returned item.

## 7. Token budgeting

- Accept a maximum output token budget.
- Reserve a portion for task summary, hard constraints and provenance.
- Rank remaining candidates and add until budget is reached.
- Estimate using the target tokenizer when available; otherwise label as approximate.
- Return actual output token count from the host only if host reports it; otherwise do not claim exact model prompt usage.
- Provide `get_more_context` behavior through a follow-up call or repeated `agentgit_get_task_context` with a narrower category.

## 8. Freshness strategy

- Associate index records with file hashes and Git commit.
- Use Git status/diff to detect changed/deleted paths.
- Mark records stale when hash differs.
- Provide explicit refresh tool.
- Before implementation, agent must inspect current file content.
- If repository has uncommitted changes, do not assume HEAD reflects working tree.

## 9. Security

- Configure allowed repository roots.
- No arbitrary shell execution from MCP tools.
- Read-only indexer by default.
- Write-back is limited to AgentGit database, not project source files.
- Redact secrets and sensitive patterns before indexing or memory retention.
- Log tool calls without logging full private source content unnecessarily.
