# AgentGit — Security, Privacy, Assumptions and Limitations

## 1. Privacy principles

- Use synthetic or consented data for demos and benchmarks.
- Keep the first MVP local by default.
- Do not log full private conversations unnecessarily.
- Do not place credentials, API keys, or personal secrets in memory.
- Provide a way to inspect and delete user data in later versions.
- Document when an optional external model provider receives conversation content.

## 2. Prompt injection and untrusted content

Conversation messages and retrieved memory are untrusted data. They must never be treated as instructions that can alter application policy, permissions, or system prompts. The MVP does not execute tools based on memory content.

## 3. Integrity

- Hash canonical snapshot manifests.
- Use database transactions for commit, restore, and merge.
- Keep historical commits append-only.
- Validate source references.
- Record user overrides and conflict resolutions.

## 4. Assumptions

- One local user/repository is sufficient for the MVP.
- A deterministic fallback is acceptable when no model is available.
- The first version can use SQLite.
- User approval is acceptable before committing proposed memory.
- Semantic merge can be deferred; explicit item selection is sufficient.

## 5. Known limitations

- Heuristic extraction may miss implicit facts.
- Summaries can distort nuance; provenance and original messages mitigate but do not eliminate this.
- Lexical retrieval is weaker than semantic retrieval for paraphrases.
- Snapshot manifests can consume storage as history grows.
- Merge conflicts require user intervention.
- Confidence values from an LLM are not automatically calibrated probabilities.

## 6. Safety behavior

When the system is uncertain whether a detail is important, retain it or ask the user rather than silently discarding it. Preserve negations, numeric values, dates, identifiers, and explicit corrections exactly.
