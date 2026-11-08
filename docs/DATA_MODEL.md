# AgentGit — Data Model

## 1. Entities

### ConversationSession
- `id`: UUID
- `title`: string, nullable
- `created_at`: UTC timestamp

### Message
- `id`: UUID
- `session_id`: UUID
- `role`: `system | user | assistant | tool`
- `content`: text
- `created_at`: UTC timestamp
- `metadata_json`: JSON, optional

### MemoryItem
- `id`: UUID
- `logical_key`: string, nullable; used to identify potentially equivalent facts
- `content`: text
- `category`: `fact | preference | decision | constraint | task | summary | other`
- `retention_action`: `retain | summarize`
- `topic`: string
- `source_message_ids`: JSON array of UUIDs
- `confidence`: float, nullable
- `rationale`: text
- `created_at`: UTC timestamp
- `supersedes_item_id`: UUID, nullable
- `is_active`: boolean

Discard decisions belong in `MemoryDecision` rather than active `MemoryItem` rows.

### MemoryDecision
- `id`: UUID
- `candidate_text`: text
- `action`: `retain | summarize | discard`
- `rationale`: text
- `source_message_ids`: JSON array
- `policy_version`: string
- `created_at`: UTC timestamp
- `user_override`: boolean

### Branch
- `id`: UUID
- `name`: string
- `head_commit_id`: UUID
- `created_from_commit_id`: UUID
- `created_at`: UTC timestamp

### Commit
- `id`: UUID
- `branch_id`: UUID
- `parent_commit_ids`: JSON array (one parent normally, two for merge)
- `message`: text
- `snapshot_hash`: string
- `created_at`: UTC timestamp
- `author`: string, default `user`

### SnapshotItem
- `commit_id`: UUID
- `memory_item_id`: UUID
- `content_at_commit`: text
- `category_at_commit`: string
- `topic_at_commit`: string
- `source_message_ids`: JSON array
- `retention_action_at_commit`: string

Snapshot rows preserve the historical state even if a current memory item is later superseded.

### AuditEvent
- `id`: UUID
- `event_type`: string
- `actor`: string
- `entity_id`: UUID
- `payload_json`: JSON
- `created_at`: UTC timestamp

## 2. Integrity rules

- Commit and snapshot records are append-only.
- `snapshot_hash` is computed from a canonical, sorted serialization of snapshot items.
- Restore creates a new commit; it never edits a prior commit.
- Merge commits record both parent IDs.
- Branch names are unique within a repository.
- Every active memory item must have at least one source message, unless explicitly user-created.
- A summary must retain provenance to the source messages used to produce it.

## 3. Example commit manifest

```json
{
  "commit_id": "c-003",
  "branch": "main",
  "parents": ["c-002"],
  "message": "Preserve database decision and compress discussion",
  "items": [
    {
      "logical_key": "project.database",
      "content": "The project uses PostgreSQL.",
      "category": "decision",
      "source_message_ids": ["m-04", "m-07"]
    }
  ]
}
```
