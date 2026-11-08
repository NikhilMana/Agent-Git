# Product Requirements Document — AgentGit 2.0

## 1. Vision

Provide a universal, version-controlled memory and intelligent context layer that compatible AI agents can consult before work and update after work.

## 2. Users and environments

- Developers using Antigravity, Claude Code, Cursor or compatible MCP clients.
- Developers building custom agents with Python/agent frameworks.
- Teams needing traceable project decisions and cross-session continuity.

Compatibility is conditional on each host's actual MCP and lifecycle capabilities. Do not claim universal automatic transcript capture.

## 3. User problem

Agents repeatedly spend context and time rediscovering project decisions, architecture, file locations and previous progress. Manual JSON export is friction. Naively injecting a large summary is risky because it may be irrelevant or stale. AgentGit should retrieve a compact, evidence-linked context for the current task.

## 4. Primary user journey

1. User opens an existing project in an MCP-compatible agent environment.
2. A small workspace rule instructs the agent to consult AgentGit at task start.
3. Agent sends task description, repository ID, branch and optional changed-file hints.
4. AgentGit retrieves relevant conversation memories and codebase metadata.
5. AgentGit returns bounded context, source references, freshness and confidence signals.
6. Agent inspects the actual relevant source files before editing.
7. After task completion, the agent sends a structured outcome to AgentGit.
8. AgentGit proposes memory updates; user/agent policy approves and commits a new version.

## 5. Functional requirements

### FR-01 MCP server
Expose AgentGit capabilities through an MCP server. Start with local stdio transport. Reuse existing application services and database.

### FR-02 Task context retrieval
Input: task, repository ID, branch, optional current file, token budget, and context categories. Output: compact task-specific context with decisions, constraints, relevant files/symbols, dependencies, unfinished work, provenance, freshness and estimated token count.

### FR-03 Conversation memory retrieval
Retrieve relevant versioned memories using exact and semantic matching. Preserve identifiers, numeric values, dates, negations and explicit decisions exactly.

### FR-04 Codebase index
Index repository metadata: relative file paths, language, symbols, imports, dependency edges, file hashes, last indexed commit and optional embeddings. Do not store a full duplicate of source files as authoritative content.

### FR-05 Incremental refresh
Refresh changed/deleted files using Git status/diff and content hashes. Provide a full re-index command for recovery.

### FR-06 Context ranking and budgeting
Rank by task relevance, exact symbol/path matches, dependency proximity, recency, branch, confidence and freshness. Enforce a token budget. Return omitted categories and an option to request more context.

### FR-07 Source-grounded behavior
Mark all retrieved information with source type and provenance. Instruct agents to inspect live source files before code modifications. Stale indexed metadata must be flagged.

### FR-08 Task write-back
Accept a structured task outcome: summary, decisions, changed files, symbols, tests run/results, unresolved issues and source commit hash. Convert to memory candidates and retain/summarize/discard using existing policy.

### FR-09 Version control
Continue using the existing immutable snapshot, branch, merge and restore implementation. MCP tools should invoke these services.

### FR-10 Host integration
Provide Antigravity setup documentation and a minimal rule. Validate host-specific capabilities individually. Do not claim every message is automatically captured unless proven.

### FR-11 User control
Allow inspection, override, deletion policy and explicit approval of memory updates. Respect repository and branch boundaries.

## 6. Non-functional requirements

- Local-first operation.
- Low overhead; measure MCP round-trip and retrieval latency.
- Bounded context output.
- Traceability and audit events.
- Secure path handling; no access outside configured repository roots.
- No execution of arbitrary shell commands from retrieved memory.
- No secrets or credentials in indexed memory.
- Graceful fallback when index or MCP server is unavailable.

## 7. Out of scope for initial 2.0 milestone

- Modifying or deleting tokens already in the active host context.
- Guaranteed access to private host conversation transcripts.
- Automatic capture for every AI product.
- Autonomous code changes by AgentGit.
- Replacing the host agent's own reasoning or source-code inspection.
- Distributed multi-user synchronization and enterprise identity management.
