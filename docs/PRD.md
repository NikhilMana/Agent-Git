# Product Requirements Document (PRD)

## 1. Product vision

Build a user-controllable, versioned memory layer that helps long-running AI agents preserve useful context across sessions while reducing unnecessary context growth.

## 2. Problem statement

Long-running agents accumulate conversation history. Keeping all history can increase context usage and inference cost; aggressive summarization can remove details; conventional retrieval may surface fragments without showing how the agent's understanding evolved. Users also need a way to inspect, correct, recover, and experiment with memory rather than relying on opaque updates.

## 3. Target users

- Developers building persistent AI agents.
- Researchers evaluating long-horizon conversational memory.
- Users who want inspectable and reversible agent memory.
- Enterprise teams that need traceability for agent context changes.

## 4. MVP objectives and success criteria

| Objective | MVP acceptance criterion |
|---|---|
| Conversation ingestion | Accept ordered messages with session and speaker metadata |
| Adaptive retention | Every candidate is assigned retain / summarize / discard, with rationale |
| Provenance | Every retained memory links to source message IDs |
| Versioning | A commit creates an immutable snapshot and parent reference |
| History | User can list commits by branch |
| Restore | Restore creates a new commit matching a previous snapshot |
| Branch | Branch starts from a selected commit and can evolve independently |
| Merge | User can select source-branch memory items to add to target branch |
| Retrieval | Query returns ranked memory items with provenance |
| User control | User can review and override proposed memory actions before commit |

## 5. Functional requirements

### FR-01 Conversation ingestion
The system shall accept a session ID and a list of messages containing message ID, role, content, and timestamp. It shall preserve original messages for provenance.

### FR-02 Candidate extraction
The system shall identify candidate facts, preferences, decisions, constraints, and unresolved tasks. For the MVP, extraction may use a local model or a deterministic fallback.

### FR-03 Retention classification
Each candidate shall receive one action:
- `retain`: preserve exact text for high-value details such as names, IDs, dates, explicit decisions, constraints, and exact technical values.
- `summarize`: compress useful but verbose context while retaining key meaning.
- `discard`: omit low-value repetition, greetings, transient filler, or irrelevant content.

Every decision must include a rationale, confidence (if available), and source message IDs. A user must be able to override the action.

### FR-04 Memory storage
Persist memory item content, type, action, topic, source references, creation time, and status.

### FR-05 Snapshot commit
The system shall create immutable snapshots of the active memory state. A commit records branch, parent commit(s), message, timestamp, and a content hash.

### FR-06 History and diff
The system shall list commits and show added, changed, and removed memory items between two snapshots.

### FR-07 Restore
Restoring a historical version shall create a new commit from that snapshot's state. Existing commits must never be modified or deleted by restore.

### FR-08 Branch
A branch shall point to a starting commit and then accept independent commits.

### FR-09 Merge
The MVP shall support explicit, user-selected memory-item merge. If two branches contain conflicting values for the same logical key, flag the conflict and require user choice. Do not silently overwrite.

### FR-10 Retrieval
The system shall retrieve relevant active memory items using embeddings when configured, otherwise lexical ranking. Results must include source references and commit context.

### FR-11 Auditability
Record classification decisions, user overrides, commits, restores, branch creation, merges, and retrieval queries.

## 6. Non-functional requirements

- Reproducibility: same deterministic input and policy configuration should yield the same fallback decisions.
- Data integrity: commits are immutable; content hashes detect accidental changes.
- Explainability: retention decisions include human-readable rationales.
- Modularity: model provider and storage backend can be replaced.
- Local-first: the MVP can run without sending conversation data to a cloud provider.
- Performance: measure latency; do not claim targets as achieved until tested.
- Privacy: sample data must be synthetic or explicitly approved.

## 7. User stories

1. As a user, I can see which facts AgentGit retained and why.
2. As a user, I can correct a memory item before committing it.
3. As a user, I can inspect prior memory versions.
4. As a user, I can restore a previous state without destroying later history.
5. As a user, I can branch memory to explore an alternative plan.
6. As a user, I can merge selected knowledge back into the main branch.
7. As a developer, I can compare memory strategies on a fixed benchmark.

## 8. Out of scope

- Automatic merging of arbitrary semantic conflicts.
- Distributed collaboration and remote synchronization.
- Access control for multiple organizations.
- Long-term production retention policies.
- Fine-tuning or training a foundation model.
