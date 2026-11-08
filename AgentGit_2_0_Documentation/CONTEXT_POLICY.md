# AgentGit Context Policy

## 1. Objective

Minimize unnecessary prompt context while preserving the information needed for correct task execution.

Do not optimize token count in isolation. Optimize task success, correctness, traceability and token efficiency together.

## 2. Context categories

- Hard constraints: exact user requirements, prohibitions, API contracts.
- Decisions: explicit architecture and implementation choices.
- Current state: completed work, unfinished work, known defects.
- Code references: relevant files, symbols, tests and dependencies.
- Conversation memory: facts not reliably represented in code.
- Supporting context: summaries and historical rationale.

## 3. Retrieval policy

- Exact identifiers and explicit decisions outrank generic semantic matches.
- Prefer current branch and repository-specific memories.
- Include provenance and freshness.
- Deduplicate repeated facts.
- Preserve negation, dates, numbers, identifiers and uncertainty.
- Do not return irrelevant memories just to fill the budget.
- Never assume a file is current because its summary is recent.

## 4. Token budget policy

- User/host supplies a maximum budget.
- Reserve space for task constraints and key decisions.
- Allocate remaining budget by relevance and freshness.
- Return estimated token count and estimation method.
- Report omitted high-ranking items.
- Allow follow-up retrieval for additional context.
- If tokenizer is unknown, label count as approximate.

## 5. Confidence and coverage

Do not report an uncalibrated number as probability. Use a transparent coverage label such as:
- `high`: direct task terms and key constraints have supporting sources.
- `partial`: some likely dependencies or history are missing.
- `low`: insufficient evidence; agent should inspect more.

Document the rule used to assign each label.

## 6. Agent execution policy

The agent must:
1. Retrieve task context.
2. Inspect current source files and tests relevant to the change.
3. Expand retrieval or search when context is incomplete.
4. Avoid broad repository scans unless necessary.
5. Validate changes with tests.
6. Write back only verified outcomes and clearly label assumptions.

## 7. Freshness and conflict policy

Live source code and current user instructions override old memory. Stale index records must be flagged. Conflicting memories should be returned as conflicts, not silently merged.
