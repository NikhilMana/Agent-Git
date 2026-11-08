# AgentGit — Implementation Plan

## Guiding principle

Implement a working vertical slice first. Do not build the dashboard before the core memory and versioning behavior works.

## Milestone 0 — Project setup
- Create repository structure.
- Set up Python environment and FastAPI.
- Configure SQLite and SQLAlchemy.
- Add pytest and lint/format configuration.
- Add `/health`.

**Exit condition:** API starts locally and database tables are created.

## Milestone 1 — Ingestion and memory decisions
- Create sessions and messages.
- Implement deterministic candidate extraction.
- Implement retain / summarize / discard policy.
- Store decisions and source-message provenance.
- Add user override endpoint or service method.

**Exit condition:** A sample conversation produces inspectable decisions.

## Milestone 2 — Snapshot and history
- Define canonical snapshot serialization.
- Compute SHA-256 snapshot hash.
- Create immutable commits.
- List branch history.
- Load a historical snapshot and verify its hash.

**Exit condition:** Repeated reads return the same snapshot; old commits cannot be modified.

## Milestone 3 — Restore and branch
- Create branch from selected commit.
- Restore snapshot by creating a new commit.
- Test that later commits remain present in history.

**Exit condition:** Demo can create a branch and restore an earlier memory state.

## Milestone 4 — Merge
- Compare source and target branch items by logical key.
- Allow explicit selection of items.
- Detect conflicting values for the same logical key.
- Require user resolution for conflicts.
- Create two-parent merge commit.

**Exit condition:** Non-conflicting merge works; conflict is visible and never silently overwritten.

## Milestone 5 — Retrieval and context builder
- Implement lexical retrieval baseline.
- Add optional embeddings after baseline works.
- Return evidence and source IDs.
- Build compact context output for an agent.

**Exit condition:** Query retrieves relevant memories and provenance.

## Milestone 6 — Optional model adapter and UI
- Add Ollama adapter for extraction/summarization.
- Keep deterministic fallback.
- Build a minimal UI for memory items, history, branches and restore.
- Add screenshots only after actual behavior works.

## Milestone 7 — Evaluation
- Freeze a test dataset.
- Run full-history, naive-summary and AgentGit conditions.
- Save raw run outputs and configuration.
- Calculate metrics and confidence intervals where appropriate.
- Record limitations.

## Team work split (four members)
- Nikhil Mana: architecture, version service, integration and technical presentation.
- K C Roopa Shetty: memory classification and summarization evaluation.
- Prakruthi D: API, persistence and data model.
- Onaiza Khan: test dataset, benchmark scripts, UI/demo documentation.

Adjust roles to actual availability and skills; all changes should be reviewed together.

## MVP demo script
1. Ingest a 15–30 message synthetic project conversation.
2. Preview retain / summarize / discard decisions.
3. Review and commit memory.
4. Show snapshot hash and history.
5. Create branch `alternative-plan`.
6. Add an alternative decision and commit.
7. Return to `main`; show the original decision is unchanged.
8. Merge one selected item or demonstrate a flagged conflict.
9. Restore a previous snapshot as a new commit.
10. Ask a retrieval question and show source messages.

## Release checklist
- Fresh environment setup documented.
- Demo data is synthetic.
- No secrets committed.
- Unit and integration tests pass.
- Benchmark results are reproducible.
- Screenshots reflect the current build.
- Known limitations are documented.
