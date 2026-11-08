# AgentGit — Versioned Context Memory Layer for AI Agents

**Project:** AgentGit  
**Problem Statement:** L&T TECHgium #52 — Efficient and User-Controllable Context Memory for Long-Running Agentic AI  
**Status:** MVP Fully Implemented & Tested  
**Team:** Nikhil Mana, K C Roopa Shetty, Prakruthi D, Onaiza Khan

---

## 1. Executive Summary

AgentGit provides a model-agnostic, inspectable, and user-controllable versioned memory layer for persistent and long-running AI agents. 

Rather than allowing conversation context to grow unbounded or relying on destructive summarization:
1. **Adaptive Retention:** Classifies incoming conversational information into `retain` (exact facts, constraints, decisions, dates, IDs), `summarize` (verbose background context), or `discard` (greetings, transient filler).
2. **Strict Provenance:** Preserves exact source-message UUIDs and rationales for every retained piece of information.
3. **Immutable Git-like Versioning:** Every memory modification creates an immutable snapshot identified by a deterministic canonical SHA-256 hash.
4. **Branching & Experiments:** Agents and users can spawn independent memory branches to explore alternative plans without corrupting the main memory baseline.
5. **Selective Merge & Conflict Detection:** Explicitly merge chosen memory items between branches with automatic detection of conflicting logical keys (refusing silent overwrites).
6. **Non-Destructive Restore:** Restoring a prior state creates a forward commit, ensuring historical auditability is never altered or deleted.
7. **Lexical & Semantic Retrieval:** Answers queries with ranked memory items, relevance scores, and verifiable source references.

---

## 2. Project Architecture & Repository Layout

```text
Agentic Git/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application entrypoint with lifespan DB creation
│   │   ├── api/                        # Typed REST API endpoints
│   │   │   ├── health.py               # /health and /api/v1/health
│   │   │   ├── sessions.py             # Conversation ingestion & message tracking
│   │   │   ├── memory.py               # Candidate extraction preview & user overrides
│   │   │   ├── repositories.py         # Multi-repository namespace management
│   │   │   ├── commits.py              # Snapshot commits & diff inspection
│   │   │   ├── branches.py             # Branch creation, history & non-destructive restore
│   │   │   ├── merge.py                # Selective item merge with conflict detection
│   │   │   ├── retrieval.py            # Lexical retrieval & agent context builder
│   │   │   └── audit.py                # Domain event audit trails
│   │   ├── core/                       # Configuration, logging & policy versions
│   │   ├── db/                         # SQLAlchemy 2.0 SQLite engine and sessions
│   │   ├── models/                     # Declarative ORM models (commits, branches, snapshots)
│   │   ├── schemas/                    # Pydantic v2 validation contracts
│   │   ├── services/                   # Modular domain logic (VersionService, Ingestion, etc.)
│   │   ├── providers/                  # DeterministicProvider and optional OllamaProvider
│   │   └── static/                     # Developer Web Dashboard Single-Page App (SPA)
│   └── tests/
│       ├── unit/                       # Unit tests (extractor, hashing, version service, retrieval)
│       └── integration/                # End-to-end API integration tests
├── docs/                               # Architectural & Technical Specifications
├── sample_data/                        # Synthetic multi-turn project conversation dataset
├── experiments/                        # Benchmark runner & raw evaluation outputs
├── demo.py                             # Live end-to-end terminal demo script
├── pyproject.toml                      # Package specifications & dependencies
└── .env.example                        # Environment variable configuration template
```

---

## 3. Quick Start & Setup

### Requirements
- Python 3.11+
- Virtual environment (recommended)

### Installation
```bash
# Clone and enter workspace
git clone <repo-url>
cd "Agentic Git"

# Install dependencies
pip install -e .
```

### Run Automated Unit and Integration Tests
```bash
python -m pytest -v
```
*Current test suite: 18 passing tests covering extraction, hashing stability, immutability, restore, branch isolation, merge conflict detection, and API endpoints.*

### Run Live End-to-End Demo Script
```bash
python demo.py
```
This executes the synthetic project conversation scenario, previews classification, commits snapshots, branches an experiment, tests merge conflicts, restores an earlier snapshot, and executes a provenance-backed retrieval query.

### Run Benchmark Evaluation
```bash
python experiments/run_benchmarks.py
```
Runs the 4-way evaluation comparison (`Full History`, `Naive Summary`, `Simple Retrieval`, and `AgentGit`) and updates `experiments/benchmark_results.json`.

### Launch Backend Server & Web Dashboard
```bash
python -m uvicorn backend.app.main:app --reload --port 8000
```
Open your browser to:
- **Interactive Web Dashboard:** [http://localhost:8000/ui](http://localhost:8000/ui) (or [http://localhost:8000](http://localhost:8000))
- **Interactive Swagger OpenAPI Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 4. Benchmark Results

Measured on the synthetic project corpus (`sample_data/conversation_project.json`):

| Metric | Full history | Naive summary | Simple retrieval | AgentGit (Measured) |
|---|---:|---:|---:|---:|
| **Context tokens (est)** | 171 | 137 | 64 | **62** |
| **Token reduction (%)** | 0.0% | 19.9% | 62.6% | **63.7%** |
| **Gold fact recall (%)** | 100.0% | 75.0% | 75.0% | **100.0%** |
| **Provenance accuracy (%)**| 0.0% | 0.0% | 50.0% | **50.0% (strict UUID links)** |
| **Median query latency** | N/A | N/A | 2.86 ms | **3.57 ms** |
| **Version integrity verified**| No | No | No | **YES (Canonical SHA-256)** |

*Raw benchmark outputs are persisted in `experiments/benchmark_results.json`.*

---

## 5. Security & Operating Principles

1. **Untrusted Data Boundary:** Conversation text and retrieved memory items are treated as passive data strings, never as instructions or executable code.
2. **Zero Opaque Mutations:** Commits and snapshots are append-only and immutable. Restores and merges create explicit new forward commits.
3. **No Silent Overwrites:** Conflicts across equivalent logical keys (`project.database`) are flagged for user review (HTTP 409) rather than silently overwritten.
4. **Local-First Reliability:** The system operates completely without cloud or external LLM dependencies using a deterministic baseline, with optional Ollama adapter capabilities.

