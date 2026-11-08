# AgentGit Context Protocol

For every substantial coding task in this workspace:

1. **Context Retrieval:** Call `agentgit_get_task_context` with the task description, repository ID (`default`), current branch (`main`), and a context token budget.
2. **Navigation Guidance:** Use the returned architectural decisions, security constraints, and referenced files/symbols as navigation guidance.
3. **Grounding in Source:** Always inspect live source files and existing tests before editing. Live files remain authoritative over indexed summaries.
4. **Targeted Exploration:** Do not perform broad, brute-force repository scans by default. Expand file reads selectively when dependencies or unresolved details require it.
5. **Freshness Verification:** If the returned index coverage is partial or stale, call `agentgit_refresh_codebase_index` or inspect the live file directly.
6. **Task Write-Back:** After completing work and validating changes with tests, call `agentgit_record_task_outcome` with verified decisions, modified files, tests run/results, and any unresolved follow-up tasks.
7. **Integrity Rule:** Never claim a test passed unless it was actually executed and verified.
8. **Security Boundary:** Never store secrets, passwords, or private API credentials in AgentGit memory or repository commits.

