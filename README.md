# AgentGit 2.0 — Versioned Context Memory & Codebase Intelligence Layer for AI Agents

**Project:** AgentGit  
**Problem Statement:** L&T TECHgium #52 — Efficient and User-Controllable Context Memory for Long-Running Agentic AI  
**Version:** 2.0 (MCP Server + Codebase Intelligence + Stdio Integration)  
**Status:** Fully Implemented, Integrated & Evaluated (26/26 Tests Passing)  
**Team:** Nikhil Mana, K C Roopa Shetty, Prakruthi D, Onaiza Khan

---

## 1. Executive Summary

AgentGit provides a model-agnostic, inspectable, and user-controllable versioned memory and codebase intelligence layer for persistent, long-running AI agents.

AgentGit 2.0 connects directly to modern agent hosts (such as **Google Antigravity**, **Claude Desktop**, and **Cursor**) via the **Model Context Protocol (MCP)** over standard I/O (stdio). It synthesizes:
1. **Versioned Context Memory:** Immutable Git-like commits, branches, conflict-aware merges, and non-destructive restores of agent decisions and constraints.
2. **Codebase AST Intelligence Indexer:** Fast, local parsing of files, symbols (classes, methods, functions), docstrings, and cross-file dependencies with strict sandbox path validation.
3. **Freshness Manager:** Real-time hash comparison between indexed records and the live working tree to prevent hallucinated edits against stale definitions.
4. **Context Orchestrator:** Task-driven multi-factor ranking and token-budgeted context assembly with transparent coverage scoring (`high`, `partial`, `low`).
5. **Agent-Initiated Write-Back:** Forward commits capturing verified task outcomes, architectural decisions, and executed tests without opaque scraping or privacy violations.

---

## 2. AgentGit 2.0 Architecture & Repository Layout

```text
Agentic Git/
├── AGENTS.md                                   # Antigravity agent protocol & context instructions
├── backend/
│   ├── app/
│   │   ├── main.py                             # FastAPI application entrypoint with lifespan DB creation
│   │   ├── mcp/
│   │   │   └── server.py                       # Stdio FastMCP Server exposing 10 tools & 3 resources
│   │   ├── api/                                # Typed REST API endpoints
│   │   │   ├── health.py                       # /health and /api/v1/health
│   │   │   ├── sessions.py                     # Conversation ingestion & message tracking
│   │   │   ├── memory.py                       # Candidate extraction preview & user overrides
│   │   │   ├── repositories.py                 # Multi-repository namespace management
│   │   │   ├── commits.py                      # Snapshot commits & diff inspection
│   │   │   ├── branches.py                     # Branch creation, history & non-destructive restore
│   │   │   ├── merge.py                        # Selective item merge with conflict detection
│   │   │   ├── retrieval.py                    # Lexical retrieval & agent context builder
│   │   │   └── audit.py                        # Domain event audit trails
│   │   ├── core/                               # Configuration, logging & policy versions
│   │   ├── db/                                 # SQLAlchemy 2.0 SQLite engine and sessions
│   │   ├── models/                             # Declarative ORM models (commits, branches, index, etc.)
│   │   │   ├── codebase_index.py               # Codebase index, symbol, and dependency models
│   │   │   ├── repository.py                   # Repository namespace
│   │   │   ├── branch.py                       # Branch tracking
│   │   │   ├── commit.py                       # Immutable commit nodes
│   │   │   ├── snapshot.py                     # Snapshot item state at commit
│   │   │   └── memory.py                       # Candidate memory items
│   │   ├── schemas/                            # Pydantic v2 validation contracts
│   │   │   ├── codebase.py                     # File, symbol, dependency schemas
│   │   │   ├── task_context.py                 # TaskContextRequest & TaskOutcomeRequest schemas
│   │   │   ├── memory.py                       # Memory creation and update schemas
│   │   │   └── commit.py                       # Commit schemas
│   │   ├── services/                           # Modular domain services
│   │   │   ├── codebase_indexer.py             # AST parsing & dependency indexing
│   │   │   ├── freshness_manager.py            # Live file vs index freshness verification
│   │   │   ├── context_orchestrator.py         # Multi-factor ranking & token budgeting
│   │   │   ├── task_writeback.py               # Task outcome to memory commit pipeline
│   │   │   ├── version_service.py              # Git-like DAG, branches, snapshots, merge
│   │   │   ├── retention.py                    # Adaptive retention policy engine
│   │   │   ├── extractor.py                    # Candidate extraction engine
│   │   │   └── retrieval.py                    # Lexical memory retrieval service
│   │   ├── providers/                          # DeterministicProvider & OllamaProvider
│   │   └── static/                             # Developer Web Dashboard Single-Page App (SPA)
│   └── tests/
│       ├── unit/                               # 22 Unit test suites (indexer, freshness, MCP, etc.)
│       └── integration/                        # 4 End-to-end API & workflow integration suites
├── experiments/
│   ├── run_agentgit2_benchmark.py              # Controlled 3-condition 2.0 benchmark runner
│   ├── agentgit2_benchmark_results.json        # Raw 3-condition benchmark data
│   ├── run_benchmarks.py                       # MVP 4-way retrieval benchmark runner
│   └── benchmark_results.json                  # MVP raw benchmark data
├── demo.py                                     # Live end-to-end terminal demo script
├── pyproject.toml                              # Dependencies and build configuration
└── .env.example                                # Configuration template
```

---

## 3. MCP Server Configuration

AgentGit 2.0 exposes a standard I/O (stdio) Model Context Protocol server.

### Configuration for Google Antigravity, Claude Desktop, or Cursor:

Add the following to your host's MCP configuration file (e.g., `~/.gemini/antigravity/mcp_config.json` or host settings):

```json
{
  "mcpServers": {
    "agentgit": {
      "command": "python",
      "args": [
        "-m",
        "backend.app.mcp.server"
      ],
      "cwd": "C:/Coding/Python/Agentic Git",
      "env": {
        "AGENTGIT_DB_PATH": "agentgit.db",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### Stdio MCP Tools (10 Tools Registered)

| Tool Name | Parameters | Description |
|---|---|---|
| `agentgit_get_task_context` | `task`, `repository_id`, `branch`, `current_file`, `max_tokens` | Returns ranked, token-budgeted decisions, constraints, symbols, and files with coverage scoring. |
| `agentgit_search_memory` | `query`, `repository_id`, `branch`, `category`, `limit` | Searches versioned memory items with lexical ranking and source message provenance. |
| `agentgit_get_file_context` | `relative_path`, `repository_id` | Retrieves indexed file outline, symbols, dependencies, and freshness status. |
| `agentgit_record_task_outcome` | `task`, `outcome_summary`, `decisions`, `changed_files`, `tests_run`, `test_results` | Creates a verified forward commit capturing task decisions, modified files, and test results. |
| `agentgit_refresh_codebase_index` | `repository_id` | Refreshes AST index and re-computes file content hashes across the codebase. |
| `agentgit_get_memory_history` | `repository_id`, `branch`, `limit` | Returns commit history DAG and snapshot changes on the specified branch. |
| `agentgit_commit_memory` | `message`, `items`, `repository_id`, `branch` | Manually commits new or updated memory items to an immutable snapshot. |
| `agentgit_create_branch` | `branch_name`, `repository_id`, `from_branch` | Creates an isolated memory branch for experimentation without mutating main. |
| `agentgit_merge_branch` | `source_branch`, `target_branch`, `selected_keys`, `repository_id` | Merges selected memory items with automatic conflict detection on duplicate logical keys. |
| `agentgit_restore_snapshot` | `target_commit_id`, `repository_id`, `branch` | Non-destructively restores historical snapshot state by creating an auditable forward commit. |

### MCP Resources (3 Resource Templates)

- `agentgit://repositories/{repository_id}/overview` — Repository metadata, active branches, and commit count.
- `agentgit://repositories/{repository_id}/branches/{branch}/memory` — Active memory snapshot and retained items.
- `agentgit://repositories/{repository_id}/index/status` — Codebase index freshness, total files, and symbol metrics.

---

## 4. Antigravity Workspace Protocol (`AGENTS.md`)

Place `AGENTS.md` in the root of your workspace to instruct the agent on proper context retrieval and write-back behavior:

```markdown
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
```

---

## 5. Controlled 3-Condition Benchmark Results

Evaluated on 10 stratified tasks across 6 categories (small changes, backend APIs, cross-file features, refactoring with dependencies, bug fixes with historical decisions, and exact constraint checks):

| Metric | Normal baseline | Rules-only | AgentGit 2.0 |
|---|---:|---:|---:|
| **Estimated supplied context tokens (avg)** | 1,039.8 | 265.3 | **318.2** |
| **Total context tokens (10 tasks)** | 10,398 | 2,653 | **3,182** |
| **Acceptance tests passed** | 0/10 (0.0%) | 0/10 (0.0%) | **10/10 (100.0%)** |
| **Constraint / Memory recall rate** | 0.0% | 10.0% | **90.0%** |
| **Files inspected per task (avg)** | 5.5 | 1.6 | **5.0** |
| **Exploration / search tool calls (avg)** | 7.5 | 2.6 | **1.0** |
| **AgentGit retrieval latency (avg)** | N/A | N/A | **14.45 ms** |
| **Stale-context incidents** | 1 | 1 | **0** |
| **Token reduction vs Baseline** | 0.0% | -74.5% | **-69.4%** |

*Raw results and per-task breakdown are saved in [`experiments/agentgit2_benchmark_results.json`](experiments/agentgit2_benchmark_results.json).*

### Key Findings:
- **Normal baseline** incurs heavy token overhead (10,398 tokens) and 7.5 tool calls per task while failing to recall critical historical constraints (e.g. RS256 algorithm enforcement, zero plaintext secrets).
- **Rules-only** successfully restricts scanning (reducing tokens by 74.5%), but still achieves only 10% constraint recall because historical decisions do not exist in code comments.
- **AgentGit 2.0** provides **69.4% token reduction** compared to baseline, achieves **90% constraint recall**, completes context retrieval in **14.45 ms**, and guards against stale edits using `FreshnessManager`.

---

## 6. Quick Start & Verification

### Requirements
- Python 3.11+
- Virtual environment (recommended)

### Installation
```bash
pip install -e .
```

### Run All Automated Tests (26 Passing)
```bash
python -m pytest -v
```

### Run the AgentGit 2.0 Benchmark Suite
```bash
python experiments/run_agentgit2_benchmark.py
```

### Run the End-to-End Terminal Demo
```bash
python demo.py
```

### Launch Backend Server & Web Dashboard
```bash
python -m uvicorn backend.app.main:app --reload --port 8000
```
- **Interactive Web Dashboard:** [http://localhost:8000/ui](http://localhost:8000/ui)
- **Interactive OpenAPI Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
