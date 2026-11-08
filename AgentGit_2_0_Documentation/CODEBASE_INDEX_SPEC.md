# Codebase Intelligence Index Specification

## 1. Purpose

Provide a compact map of a repository so an agent can locate relevant implementation areas without repeatedly loading broad, unrelated file content.

## 2. Index records

### Repository
- repository ID
- canonical root
- default branch
- latest indexed Git commit
- index version
- last full/incremental refresh time

### File record
- relative path
- language
- size
- content hash
- last indexed time
- indexed Git commit
- ignored/excluded status
- optional short file summary

### Symbol record
- symbol name
- symbol kind: class/function/method/interface/constant
- relative path
- line range
- signature
- docstring/short description if present
- content hash

### Dependency edge
- source file
- target file/module
- relation: imports/calls/extends/implements/references
- evidence source
- confidence or parser certainty

## 3. Indexing rules

- Respect `.gitignore`.
- Add configurable exclusions for `.env`, secrets, keys, `node_modules`, `.venv`, build directories, generated assets and binaries.
- Resolve paths and symlinks; reject traversal outside repository root.
- Never execute indexed files.
- Do not index secret values.
- Store metadata and bounded snippets, not an uncontrolled duplicate of all source.
- Keep source file hash so staleness can be detected.

## 4. Incremental indexing

1. Read Git status and changed paths.
2. Hash changed files.
3. Remove records for deleted files.
4. Parse changed files only.
5. Update symbol and dependency records.
6. Store current index revision.
7. Return a refresh report.

For uncommitted files, record working-tree hashes separately from the last Git commit.

## 5. Retrieval

Candidate generation:
- exact filename/path
- symbol and identifier matches
- lexical search
- dependency neighbors
- optional vector similarity

Ranking should favor:
1. Exact symbol/path references from the task.
2. Files directly implementing the requested feature.
3. Dependencies and tests for those files.
4. Recent, relevant architecture decisions.
5. General summaries only when needed.

## 6. Freshness

A record is fresh only when the live file hash matches the indexed hash. If not, mark it stale and do not present indexed snippets as current truth.

## 7. MVP scope

Start with Python and TypeScript/JavaScript support if those languages exist in the repository. Use Tree-sitter or suitable parsers after inspecting project dependencies. Unsupported languages must fall back gracefully to path and lexical indexing.
