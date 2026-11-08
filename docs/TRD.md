# Technical Requirements Document (TRD)

## 1. Engineering approach

Build a modular monolith for the MVP. Keep API, domain logic, persistence, model adapters, and evaluation separate. Avoid microservices until there is evidence they are needed.

## 2. Technology choices

| Layer | MVP choice | Reason |
|---|---|---|
| Runtime | Python 3.11+ | Fast iteration and AI ecosystem |
| API | FastAPI | Typed REST API and automatic OpenAPI |
| Validation | Pydantic v2 | Request / response validation |
| ORM | SQLAlchemy 2.x | Portable persistence |
| Local DB | SQLite | Zero-configuration development |
| Optional DB | PostgreSQL + pgvector | Later scale and vector retrieval |
| Local LLM | Ollama adapter | Optional local inference |
| Embeddings | sentence-transformers adapter | Optional semantic retrieval |
| Tests | pytest | Unit and integration tests |
| Frontend | React + TypeScript | Optional dashboard after API works |

## 3. Core modules

### 3.1 IngestionService
Validates messages, assigns stable IDs if missing, stores raw message records, and creates a session association.

### 3.2 CandidateExtractor
Produces candidate memory records. Interface:
`extract(messages) -> list[MemoryCandidate]`

Implement a deterministic extractor first. Add an LLM adapter behind the same interface.

### 3.3 RetentionPolicy
Classifies each candidate as retain, summarize, or discard. Inputs include candidate text, category, source, recency, repetition, explicitness, and user policy. Output includes action and rationale.

### 3.4 Summarizer
Compresses selected candidates. It must preserve named entities, numeric values, dates, negations, constraints, and explicit decisions. Store source references and the original text so summaries remain traceable.

### 3.5 MemoryRepository
CRUD for memory items and raw messages. The repository must not implement version-control semantics.

### 3.6 VersionService
Creates commits, snapshots, branches, restores, diffs, and merges. A commit is immutable. Store the complete snapshot manifest or a content-addressed manifest so historical states can be reconstructed.

### 3.7 RetrievalService
Ranks active memory items. MVP fallback: normalized lexical overlap / BM25-style ranking. Optional: embedding similarity. Return evidence and provenance, not just text.

### 3.8 ModelProvider
A provider interface for classify, extract, summarize, and embed. Provide:
- `DeterministicProvider` (always available)
- `OllamaProvider` (optional)
- `EmbeddingProvider` (optional)

## 4. Versioning semantics

- A branch has a name and a head commit.
- A commit has a unique ID, one or more parent commit IDs, branch ID, message, timestamp, and snapshot hash.
- A snapshot is immutable and represents the exact active memory state at that commit.
- Creating a commit advances only the selected branch head.
- Restore does not move history backward destructively; it creates a new commit containing the restored snapshot state.
- Branch creation points a new branch head to an existing commit.
- Merge creates a new commit with two parents and a merged snapshot.
- The MVP uses explicit selection for merge conflicts. No silent last-write-wins behavior.

## 5. Suggested API endpoints

See `API_SPEC.md`. All endpoints should return stable IDs and structured errors.

## 6. Configuration

Use environment variables:
- `DATABASE_URL` (default local SQLite)
- `OLLAMA_BASE_URL` (optional)
- `OLLAMA_MODEL` (optional)
- `EMBEDDING_MODEL` (optional)
- `AGENTGIT_MODE` (`deterministic` or `ollama`)
- `LOG_LEVEL`

Never commit secrets or API keys.

## 7. Reliability and observability

- Structured logs with request ID.
- Domain events for commit, restore, branch, merge, and override.
- Database transactions for all version operations.
- Content hash validation when loading a snapshot.
- Clear error for unknown commit, branch, session, or memory item.

## 8. Testing requirements

- Unit tests for retention policy and content hashing.
- Integration tests for commit/history/restore/branch/merge.
- API tests for validation and error handling.
- Property tests or repeated tests proving old commits remain unchanged.
- Benchmark tests separated from unit tests.
