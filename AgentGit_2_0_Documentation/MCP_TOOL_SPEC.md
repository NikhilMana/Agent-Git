# AgentGit MCP Tool Specification

## Design principles

- MCP is an integration protocol, not an automatic transcript tap.
- Tools invoke existing AgentGit core services.
- The host agent decides when to call tools, guided by workspace rules.
- All outputs are bounded, provenance-aware and safe to treat as untrusted data.
- Do not return an entire repository or entire conversation by default.

## 1. `agentgit_get_task_context`

Purpose: Return compact, task-specific memory and codebase context.

Input:
```json
{
  "task": "Implement refresh token authentication",
  "repository_id": "repo-123",
  "branch": "main",
  "current_file": null,
  "max_tokens": 3500,
  "include": [
    "decisions",
    "constraints",
    "files",
    "symbols",
    "dependencies",
    "unfinished_tasks",
    "conversation_memories"
  ]
}
```

Output shape:
```json
{
  "repository_id": "repo-123",
  "branch": "main",
  "context_sections": {
    "decisions": [],
    "constraints": [],
    "unfinished_tasks": []
  },
  "relevant_files": [],
  "symbols": [],
  "dependencies": [],
  "memory_items": [],
  "estimated_tokens": 0,
  "token_estimation_method": "approximate",
  "coverage": "partial",
  "needs_more_context": false,
  "omitted_items": [],
  "sources": []
}
```

## 2. `agentgit_search_memory`

Search conversation and project memories. Return ranked items with source message IDs, branch, commit and score explanation.

## 3. `agentgit_get_file_context`

Input repository ID, relative file path, optional symbol and budget. Return indexed metadata and relevant snippets only when authorized. Mark stale records.

## 4. `agentgit_record_task_outcome`

Input:
- repository ID and branch
- task description
- concise outcome summary
- decisions made
- files changed
- symbols changed
- tests run and results
- unresolved issues
- Git commit hash if available

Validate and convert fields to candidate memory items. Do not automatically commit if user approval is required by repository policy.

## 5. `agentgit_refresh_codebase_index`

Refresh full or changed paths. Restrict operation to configured repository root. Return indexed, skipped, deleted and stale counts.

## 6. Version-control tools

Wrap existing services:
- `agentgit_get_memory_history`
- `agentgit_commit_memory`
- `agentgit_create_branch`
- `agentgit_merge_branch`
- `agentgit_restore_snapshot`

Preserve immutable snapshots and explicit conflict resolution.

## 7. Optional resources

- `agentgit://repositories/{repository_id}/overview`
- `agentgit://repositories/{repository_id}/branches/{branch}/memory`
- `agentgit://repositories/{repository_id}/index/status`

Resources are read-only. Do not use resource reads for mutations.

## 8. Error behavior

Return structured, actionable errors:
- `REPOSITORY_NOT_AUTHORIZED`
- `REPOSITORY_NOT_FOUND`
- `BRANCH_NOT_FOUND`
- `INDEX_STALE`
- `TOKEN_BUDGET_INVALID`
- `MEMORY_NOT_FOUND`
- `MERGE_CONFLICT`
- `SERVICE_UNAVAILABLE`

Do not leak absolute paths outside the authorized repository.
