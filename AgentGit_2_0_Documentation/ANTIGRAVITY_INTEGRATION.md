# Antigravity Integration Guide

## 1. Goal

Connect Antigravity to AgentGit through a local MCP server and a lightweight workspace instruction file.

This integration supports agent-initiated context retrieval and write-back. It does not by itself guarantee automatic capture of every private chat message.

## 2. MCP server configuration

After implementing the actual server entry point, configure Antigravity's MCP settings using the command and arguments that match this repository.

Illustrative configuration only:
```json
{
  "mcpServers": {
    "agentgit": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "ABSOLUTE_PATH_TO_AGENTGIT",
        "python",
        "-m",
        "agentgit_mcp.server"
      ],
      "env": {
        "AGENTGIT_CONFIG": "ABSOLUTE_PATH_TO_AGENTGIT/config/agentgit.toml"
      }
    }
  }
}
```

Do not copy the module name or paths until confirmed against the implemented project.

## 3. Workspace rule

Create a short `AGENTS.md` or supported workspace instruction file:

```markdown
# AgentGit Context Protocol

For each substantial task in this workspace:

1. Call `agentgit_get_task_context` with the task, repository ID,
   current branch and a reasonable context budget.
2. Use returned decisions, constraints and file/symbol references
   as navigation guidance.
3. Inspect current source files and tests before editing.
4. If the returned coverage is partial/low, request more context
   or search the repository.
5. Do not treat memory summaries as source-code truth.
6. Do not scan the entire repository by default; expand only when
   task dependencies require it.
7. After completing work, call `agentgit_record_task_outcome`
   with verified decisions, changed files, tests and unresolved issues.
8. Do not claim a test passed unless it was actually run.
9. Do not store secrets or sensitive credentials in AgentGit.
```

Keep this instruction concise. Avoid putting the full project architecture in always-loaded rules.

## 4. Manual validation

- Confirm AgentGit MCP server starts.
- Confirm Antigravity discovers the tools.
- Ask a task that should retrieve a known prior decision.
- Confirm the tool returns correct provenance.
- Change a source file and confirm stale index detection.
- Ask the agent to inspect the file before editing.
- Complete a task and invoke write-back.
- Start a new session and confirm the saved decision is retrievable.

## 5. Automatic capture investigation

Investigate whether the installed Antigravity version exposes supported lifecycle hooks, session events, extension APIs or conversation-history export. Do not scrape private application databases or rely on undocumented internal storage.

If no supported automatic capture API exists, use explicit `agentgit_record_task_outcome` calls from the agent and optionally a user-invoked capture command. Describe this honestly as agent-assisted capture, not automatic transcript synchronization.
